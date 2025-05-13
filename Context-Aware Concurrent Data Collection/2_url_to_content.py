import os
import pandas as pd
import re
import requests
import json
import time
import logging
from urllib.parse import urlparse
from newspaper import Config, Article
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
import hashlib
import pickle

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('url_to_content.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 10
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_WORKERS = 10  # Number of concurrent threads

# Current directory and dataset path
current_dir = os.path.dirname(os.path.abspath(__file__))
datasets_file_path = os.path.join(current_dir, '../dataset/')

# Cache management
CACHE_FILE = os.path.join(current_dir, 'url_content_cache.pkl')

def load_cache():
    """Load URL cache file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Cache loading error: {e}")
    return {}

def save_cache(cache):
    """Save URL cache file"""
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache, f)
    except Exception as e:
        logger.error(f"Cache saving error: {e}")

# Load URL content cache
url_cache = load_cache()

def get_datetime_folders():
    """Get list of date folders from dataset directory"""
    if not os.path.exists(datasets_file_path):
        logger.error(f"Dataset path does not exist: {datasets_file_path}")
        return []
    
    folders = [folder for folder in os.listdir(datasets_file_path) 
               if os.path.isdir(os.path.join(datasets_file_path, folder))]
    return sorted(folders, reverse=True)

def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Retry decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {e}. Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
            logger.error(f"All retry attempts failed: {last_exception}")
            return None
        return wrapper
    return decorator

def clean_text(text):
    """Clean text: remove newlines and quotes"""
    if not text:
        return None
    text = re.sub(r'[\n"\'""'']', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text if text else None

@retry_on_failure()
def process_msn(url):
    """Process MSN news URL"""
    logger.info(f"Starting MSN processing: {url}")
    match = re.search(r'/ar-([^?]+)', url)
    if not match:
        logger.error(f"Could not extract ID from URL: {url}")
        return None
    
    extracted_part = match.group(1)
    msn_url = f"https://assets.msn.com/content/view/v2/Detail/en-us/{extracted_part}"
    
    response = requests.get(msn_url)
    if response.status_code != 200:
        logger.error(f"MSN API request failed ({response.status_code}): {url}")
        return None
    
    try:
        data = json.loads(response.text)
        if 'body' not in data:
            logger.error(f"No 'body' key in JSON response: {url}")
            return None
        
        article = Article(url="")
        article.download(input_html=data['body'])
        article.parse()
        text = clean_text(article.text)
        
        if text:
            logger.info(f"MSN processing completed: {url}")
            return text
        logger.warning(f"No text extracted: {url}")
        return None
    except Exception as e:
        logger.error(f"MSN processing error: {url}, {e}")
        raise

@retry_on_failure()
def process_other(url):
    """Process regular URL"""
    logger.info(f"Starting regular URL processing: {url}")
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        text = clean_text(article.text)
        if text:
            logger.info(f"Regular URL processing completed: {url}")
            return text
        raise ValueError("Text extraction failed")
    except Exception as e:
        logger.warning(f"newspaper3k failed: {url}, {e}")
        
        # Retry with Scrappey API
        logger.info(f"Attempting with Scrappey: {url}")
        api_url = 'https://publisher.scrappey.com/api/v1?key=[your_api_key]'
        headers = {'Content-Type': 'application/json'}
        data = {
            'cmd': 'request.get',
            'url': url,
        }
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code != 200:
            logger.error(f"Scrappey API response error ({response.status_code}): {url}")
            raise ValueError(f"Scrappey API response error: {response.status_code}")
        
        response_json = response.json()
        html_content = response_json.get('solution', {}).get('response', '')
        
        if not html_content:
            logger.error(f"No HTML received from Scrappey: {url}")
            raise ValueError("Empty HTML returned from Scrappey")
        
        article = Article(url="")
        article.download(input_html=html_content)
        article.parse()
        text = clean_text(article.text)
        
        if text:
            logger.info(f"Scrappey processing completed: {url}")
            return text
        logger.warning(f"Text extraction failed with Scrappey too: {url}")
        raise ValueError("Text extraction failed with Scrappey too")

def get_url_content(url):
    """Extract content from URL (using cache)"""
    if pd.isna(url) or not url:
        return None
    
    # Check cache
    if url in url_cache:
        logger.debug(f"Using content from cache: {url}")
        return url_cache[url]
    
    # Process based on URL type
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        if 'msn.com' in domain:
            content = process_msn(url)
        else:
            content = process_other(url)
        
        # Save to cache
        if content:
            url_cache[url] = content
            # Periodically save cache (based on hash value)
            if hash(url) % 10 == 0:  # Save after ~10% of URLs processed
                save_cache(url_cache)
        
        return content
    except Exception as e:
        logger.error(f"Content extraction failed: {url}, {e}")
        return None

def process_csv(path, file_name):
    """Process CSV file"""
    full_path = os.path.join(path, file_name)
    logger.info(f"Starting CSV processing: {full_path}")
    
    try:
        df = pd.read_csv(full_path)
        
        if 'url' not in df.columns:
            logger.warning(f"No 'url' column found: {full_path}")
            return
        
        # Filter rows without URLs
        df_with_urls = df[~df['url'].isna() & (df['url'] != '')].copy()
        df_without_urls = df[df['url'].isna() | (df['url'] == '')].copy()
        
        if df_with_urls.empty:
            logger.warning(f"No URLs to process: {full_path}")
            return
        
        # Parallel processing
        urls = df_with_urls['url'].tolist()
        logger.info(f"Starting processing of {len(urls)} URLs: {file_name}")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit URLs and map results
            future_to_url = {executor.submit(get_url_content, url): url for url in urls}
            
            # Dictionary to track results
            url_to_content = {}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content = future.result()
                    url_to_content[url] = content
                except Exception as e:
                    logger.error(f"Error processing URL: {url}, {e}")
                    url_to_content[url] = None
        
        # Apply results to dataframe
        df_with_urls['Article_Content'] = df_with_urls['url'].map(url_to_content)
        
        # Add None for rows without URLs
        if not df_without_urls.empty:
            df_without_urls['Article_Content'] = None
            
        # Merge dataframes
        df_result = pd.concat([df_with_urls, df_without_urls])
        
        # Save results
        new_path = path.replace('sigir_datasets', 'sigir_results')
        os.makedirs(new_path, exist_ok=True)
        
        new_file_path = os.path.join(new_path, file_name)
        df_result.to_csv(new_file_path, index=False)
        logger.info(f"CSV processing completed: {full_path} -> {new_file_path}")
        
    except Exception as e:
        logger.error(f"CSV processing error: {full_path}, {e}")

def process_directory(datetime_range, pir_range, pf_range):
    """Traverse directories and process files"""
    start_date = datetime.strptime(datetime_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(datetime_range[1], "%Y-%m-%d")
    datetime_folders = get_datetime_folders()
    
    for datetime_folder in datetime_folders:
        try:
            folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
            if folder_date < start_date or folder_date > end_date:
                logger.info(f"Skipping folder outside date range: {datetime_folder}")
                continue
            
            folder_path = os.path.join(datasets_file_path, datetime_folder)
            if not os.path.isdir(folder_path):
                continue
                
            pir_folders = [folder for folder in os.listdir(folder_path) 
                          if os.path.isdir(os.path.join(folder_path, folder))]
                
            for pir_folder in pir_folders:
                if pir_folder in pir_range:
                    logger.info(f"Skipping PIR folder as configured: {pir_folder}")
                    continue
                    
                pir_folder_path = os.path.join(folder_path, pir_folder)
                pf_folders = [folder for folder in os.listdir(pir_folder_path) 
                             if os.path.isdir(os.path.join(pir_folder_path, folder))]
                    
                for pf_folder in pf_folders:
                    if pf_folder in pf_range:
                        logger.info(f"Skipping PF folder as configured: {pf_folder}")
                        continue
                        
                    pf_folder_path = os.path.join(pir_folder_path, pf_folder)
                    csv_files = [file for file in os.listdir(pf_folder_path) if file.endswith('.csv')]
                    
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        # Process multiple CSV files in parallel
                        csv_path = os.path.join(folder_path, pir_folder, pf_folder)
                        executor.map(lambda file: process_csv(csv_path, file), csv_files)
                        
        except Exception as e:
            logger.error(f"Directory processing error: {datetime_folder}, {e}")

def main():
    """Main function"""
    start_time = time.time()
    logger.info("Starting URL content extraction")
    
    datetime_range = ['2023-09-24', '2024-08-04']
    pir_range = ['google_news']  # PIR folders to skip
    pf_range = []  # PF folders to skip
    
    try:
        process_directory(datetime_range, pir_range, pf_range)
        
        # Save cache after completion
        save_cache(url_cache)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Task completed! Total time: {elapsed_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error during processing: {e}")
    finally:
        # Save cache on exit
        save_cache(url_cache)

if __name__ == '__main__':
    main()