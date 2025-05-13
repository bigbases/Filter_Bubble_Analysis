import requests
import pandas as pd
import os
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import botocore
import boto3
import random
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Serverless_Functions.aws_update import LambdaUpdater

current_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json(file_name):
    file_path = os.path.join(current_dir, file_name)
    with open(file_path, 'r') as file:
        return json.load(file)

def invoke_lambda(client, arn, payload, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.invoke(FunctionName=arn, Payload=payload, InvocationType="RequestResponse")
            return json.loads(response['Payload'].read().decode('utf-8'))
        except Exception as e:
            logging.error(f"Error invoking Lambda function (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

def fetch_data(topic, region, aws_function, created_date):
    logging.info(f"Fetching data for Google News: topic={topic}, region={region} aws_function={aws_function}")
    source_list, title_list, content_list, url_list, page_list, rake_list = [], [], [], [], [], []

    arn = aws_function['arn']
    region_name = aws_function['region']

    session = boto3.session.Session()
    client_config = botocore.config.Config(
        read_timeout=100, 
        connect_timeout=100, 
        retries={"max_attempts": 3}
    )
    client = session.client('lambda',
                            aws_access_key_id="",
                            aws_secret_access_key="",
                            config=client_config,
                            region_name=region_name)

    start = 0
    while True:
        try:
            import browser_cookie3
            cookie_file = load_json('cookies.json')['neutral']
            cookies = browser_cookie3.chrome(domain_name='google.com', cookie_file=cookie_file['file'])
            cookies = {cookie.name: cookie.value for cookie in cookies}
            if region in ['eu-west-3', 'eu-west-2']:
                random_cookies = random.sample(cookies.keys(), random.randint(1, len(cookies)))
                cookies = {name: value for name, value in cookies.items() if name in random_cookies}
            else:
                # List of the desired cookies
                cookie_names = ['AEC', 'NID', 'DV']

                # Randomly select a combination of the cookies (at least one, up to all three)
                random_cookies = random.sample(cookie_names, random.randint(1, len(cookie_names)))

                # Filter the cookies to include only the randomly selected combination
                cookies = {name: value for name, value in cookies.items() if name in random_cookies}
            headers = load_json('accept_language.json')['en-US']
            
            topic_params = {
                'q': topic,
                'tbm': 'nws',
                'start': str(start) if start > 0 else None,
            }
            topic_params = {k: v for k, v in topic_params.items() if v is not None}
            
            url = 'https://www.google.com/search'
            payload = json.dumps({
                "url": url,
                "params": topic_params,
                "cookies": cookies,
                "headers": headers
            })
            
            response = invoke_lambda(client, arn, payload)
            if not response:
                logging.warning(f"No response from Lambda function for topic={topic}, region={region}")
            
            soup = BeautifulSoup(response['body'], 'html.parser')
            results = soup.find_all('div', class_='SoaBEf')

            if not results:
                results = soup.find_all('div', class_='W0kfrc')
                if not results:
                    logging.info(f"No results found: start={start}, region={region}, topic={topic}")
                    LambdaUpdater().update_lambda_functions(region_name, arn)

            elif results:
                for result in results:
                    try:
                        source = result.find('div', class_='MgUUmf NUnG9d')
                        source = source.text.strip() if source else ""
                        source_list.append(source)

                        title = result.find('div', class_='n0jPhd ynAwRc MBeuO nDgy9d')
                        title = title.text.replace("\n", "").strip() if title else 'Title Not Found'
                        title_list.append(title)

                        content = result.find('div', class_='GI74Re nDgy9d')
                        content = content.text.replace("\n", "").strip() if content else ""
                        content_list.append(content)

                        url_block = result.find('a', class_='WlydOe')
                        url = url_block['href'] if url_block else ""
                        url_list.append(url)

                        page_list.append((start) // 10 + 1)
                        rake_list.append(len(title_list))

                        if len(title_list) > 50 or start > 50:
                            break
                    except Exception as e:
                        logging.error(f"Error processing result: {str(e)}")
                        continue
                
                logging.info(f"topic={topic:<20}|PF setting={region_name:<10}|page={start//10 + 1:<5}|count={len(title_list):<5}")
                start += 10
                time.sleep(random.uniform(60, 90))

            if len(title_list) > 50 or start > 50:
                break

        except Exception as e:
            logging.error(f"Error in fetch_data: {aws_function} | {str(e)}")
            LambdaUpdater().update_lambda_functions(region, arn)
            time.sleep(random.uniform(60, 90))
            continue

    search_results_dir_path = os.path.join(current_dir, f"../../dataset/{created_date}/google_news/region")
    os.makedirs(search_results_dir_path, exist_ok=True)
    
    df = pd.DataFrame({
        'page': page_list,
        'rank': rake_list,
        'source': source_list,
        'title': title_list,
        'content': content_list,
        'url': url_list
    })
    
    csv_path = f"{search_results_dir_path}/{topic}_{region}.csv"
    df.to_csv(csv_path, index=False)
    logging.info(f"Data saved to {csv_path}")

def process_group(topics, regions, created_date):
    with ThreadPoolExecutor(max_workers=60) as executor:
        futures = []
        scraper_num = 1

        for topic in topics:
            for region in regions:
                aws_function = {
                    "region": region,
                    "arn": f"arn:aws:lambda:{region}:390844758754:function:scraper_{scraper_num}"
                }
                future = executor.submit(fetch_data, topic, region, aws_function, created_date)
                futures.append(future)
            scraper_num += 1

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"An error occurred in a thread: {str(e)}")

    logging.info("Completed processing all topics")

def start(created_date):
    topic_file_path = os.path.join(current_dir, '../topic.csv')
    topics = pd.read_csv(topic_file_path)['query'].tolist()

    regions = ['us-west-1', 'us-east-2', 'ap-northeast-2', 'ap-northeast-1', 'eu-west-2', 'eu-west-3']

    process_group(topics, regions, created_date)
