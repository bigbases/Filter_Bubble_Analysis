import os
import pandas as pd
import re
import requests
import json
from urllib.parse import urlparse
from newspaper import Config, Article
from datetime import datetime

# Get the list of folders in the PIR_Data directory
current_dir = os.path.dirname(os.path.abspath(__file__))
datasets_file_path = os.path.join(current_dir, 'datasets')
datetime_folders = [folder for folder in os.listdir(datasets_file_path)]
datetime_folders = sorted(datetime_folders, reverse=True)
print(datetime_folders)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 10

# Dictionary to cache processed URLs and their content
url_cache = {}

def process_directory(datetime_range, pir_range, pf_range):
    start_date = datetime.strptime(datetime_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(datetime_range[1], "%Y-%m-%d")

    for datetime_folder in datetime_folders:
        folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
        if folder_date < start_date or folder_date > end_date:
            print("Skipping", datetime_folder)
            continue
        folder_path = os.path.join(datasets_file_path, datetime_folder)
        print("folder_path", folder_path)
        if os.path.isdir(folder_path):  # Check if the path is a directory
            pir_folders = [folder for folder in os.listdir(folder_path)]
            pir_path = os.path.join(datasets_file_path, datetime_folder)

            for pir_folder in pir_folders:
                ################################################################################################
                if pir_folder in pir_range:
                    continue
                pir_folder_path = os.path.join(pir_path, pir_folder)

                if os.path.isdir(pir_folder_path):  # Check if the path is a directory
                    pf_folders = [folder for folder in os.listdir(pir_folder_path)] # csv 파일만
                    pf_path = os.path.join(datasets_file_path, datetime_folder, pir_folder)

                    for pf_folder in pf_folders:
                        ################################################################################################
                        if pf_folder in pf_range:
                            continue
                        pf_folder_path = os.path.join(pf_path, pf_folder)

                        if os.path.isdir(pf_folder_path):  # Check if the path is a directory
                            csv_files = [file for file in os.listdir(pf_folder_path) if file.endswith('.csv')]
                            final_path = os.path.join(datasets_file_path, datetime_folder, pir_folder, pf_folder)

                            for file in csv_files:
                                process_csv(final_path, file)
                                # if 'Biden Trump' in file:
                                #     process_csv(final_path, file)

def process_csv(final_path, file_name):
    print(f"Processing {final_path}/{file_name}")
    try:
        df = pd.read_csv(os.path.join(final_path, file_name))

        if 'url' in df.columns:
            detail_content_list = []
            for url in df['url']:
                if pd.isna(url):  # NaN 값 체크
                    detail_content = None
                elif url in url_cache:
                    detail_content = url_cache[url]
                    print(f"Using cached content for {url}")
                else:
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc
                    if 'msn.com' in domain:
                        detail_content = process_msn(url)
                    else:
                        detail_content = process_other(url)
                    if detail_content:  # detail_content가 None이 아닌 경우에만 캐시에 저장
                        url_cache[url] = detail_content
                detail_content_list.append(detail_content)
            df['Article_Content'] = detail_content_list
            new_final_path = final_path.replace('datasets', 'datasets_with_content')
            if not os.path.exists(new_final_path):
                os.makedirs(new_final_path)
            new_file_path = os.path.join(new_final_path, f"{file_name}")
            df.to_csv(new_file_path, index=False)
            print(f"Updated file saved as {new_file_path}")
        else:
            print(f"No 'URL' column found in {final_path}.")
    except Exception as e:
        print(f"Error processing {final_path}/{file_name}: {e}")
        

def process_msn(url):
    match = re.search(r'/ar-([^?]+)', url)
    if match:
        try:
            extracted_part = match.group(1)
            msn_url = f"https://assets.msn.com/content/view/v2/Detail/en-us/{extracted_part}"
            response = requests.get(msn_url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if 'body' in data:
                    body = data['body']
                    article = Article(url="")
                    article.download(input_html=body)
                    article.parse()
                    text = clean_text(article.text)
                    if text:
                        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                        print(url, ": msn done")
                        return text
                    else:
                        print("WARNING: No text found for", url)
                        return None
                else:
                    print("ERROR: 'body' key not found in the JSON response for", url)
                    return None
            else:
                print(f"ERROR: Failed to fetch data for {url} with status code {response.status_code}")
                return None
        except Exception as e:
            print("ERROR: extracted_part", extracted_part, url, e)
            return None
    else:
        print("ERROR: Could not extract part from URL", url)
        return None


def process_other(url):
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        text = clean_text(article.text)
        if text:
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            print(url, ": article done")
            return text
        else:
            raise ValueError("No text found after parsing")
    except Exception as e:
            print(f"Selenium failed for {url}: {e}. Trying Scrappey...")
            try:
                api_url = 'https://publisher.scrappey.com/api/v1?key={scrappey_api_key}'
                headers = {'Content-Type': 'application/json'}
                data = {
                    'cmd': 'request.get',
                    'url': url,
                }
                response = requests.post(api_url, headers=headers, json=data)
                response_json = response.json()
                html_content = response_json.get('solution', {}).get('response', '')
                article = Article(url="")
                article.download(input_html=html_content)
                article.parse()
                text = clean_text(article.text)
                if text:
                    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                    print(url, ": scrappy done")
                    return text
                else:
                    return None
            except Exception as scrappey_error:
                print(f"Scrappey failed for {url}: {scrappey_error}")
                return None


def clean_text(text):
    return re.sub(r'[\n"\'“”‘’]', ' ', text)


if __name__ == '__main__':
    datetime_range = ['2023-09-24', '2026-08-04']
    # pir_range = ['google_news', 'bing_news']
    pir_range = []
    pf_range = []
    try:
        process_directory(datetime_range, pir_range, pf_range)
    except Exception as e:
        print(e)