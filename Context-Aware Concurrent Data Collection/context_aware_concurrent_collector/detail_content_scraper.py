import requests
import time
import json
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import browser_cookie3

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.aws_client import AWSLambdaClient
from core.utils import retry_on_failure, random_sleep, format_log_message
from parsers.bing_news_parser import BingNewsParser
from parsers.google_news_parser import GoogleNewsParser



class DetailContentScraper:
    """Detailed content scraper class"""
    
    def __init__(self, scraper_name: str = 'bing_news'):
        self.scraper_name = scraper_name
        self.aws_clients = {}
        self.cookies_cache = {}  # Cookie cache
        
        # Initialize parser
        if scraper_name == 'bing_news':
            self.parser = BingNewsParser()
        elif scraper_name == 'google_news':
            self.parser = GoogleNewsParser()
        else:
            raise ValueError(f"Unsupported scraper: {scraper_name}")
        

        
        # Default settings (can be overridden by environment variables or settings)
        self.max_pages_per_query = int(os.environ.get('MAX_PAGES_PER_QUERY', 20))  # Maximum number of pages
        self.items_per_page = 10  # Number of articles per page
        self.max_articles_per_query = self.max_pages_per_query * self.items_per_page  # Dynamic calculation
        
    def setup_aws_clients(self, aws_configs: List[Dict[str, Any]]):
        """Setup AWS clients"""
        for aws_config in aws_configs:
            region = aws_config['body'].get('region', 'us-east-1')
            if region not in self.aws_clients:
                self.aws_clients[region] = AWSLambdaClient(region)
        

    
    def load_cookies_from_file(self, cookie_file_path: str, domain_name: str) -> Dict[str, str]:
        """Load cookies from Chrome cookie file (using cache)"""
        if cookie_file_path in self.cookies_cache:
            return self.cookies_cache[cookie_file_path]
        
        try:
            print(f'domain_name: {domain_name}')
            # print(f"🍪 Loading cookie file: {cookie_file_path}")
            if domain_name == 'bing_news':
                cookies = browser_cookie3.chrome(domain_name='bing.com', cookie_file=cookie_file_path)
            elif domain_name == 'google_news':
                cookies = browser_cookie3.chrome(domain_name='google.com', cookie_file=cookie_file_path)

            cookie_dict = {cookie.name: cookie.value for cookie in cookies}
            # print(cookie_dict)
            # Save to cache
            self.cookies_cache[cookie_file_path] = cookie_dict
                            # print(f"Cookie loading successful: {len(cookie_dict)} items")
            return cookie_dict
            
        except Exception as e:
                            # print(f"Cookie loading failed: {str(e)}")
                # print(f"Proceeding with empty cookies")
            # Save empty dictionary to cache (prevent retry)
            self.cookies_cache[cookie_file_path] = {}
            return {}
    
    @retry_on_failure(max_retries=3)
    def scrape_bing_news(self, topic: str, queries: List[str], perspective: str = "", 
                        cookies: Dict = None, headers: Dict = None) -> List[Dict[str, Any]]:
        """Bing News scraping (AWS Lambda only)"""
        # Remove local requests - use AWS Lambda only
        logging.warning("Local scraping not allowed. Use AWS Lambda through concurrent_scraping method.")
        return []
    
    def scrape_with_aws_lambda(self, query: str, perspective: str, 
                              aws_config: Dict, cookies: Dict, headers: Dict, 
                              mode: str = "news", max_articles: int = None, topic: str = None, 
                              distinguishing_value: str = None) -> List[Dict[str, Any]]:
        """Scraping through AWS Lambda (with pagination support)"""
        if max_articles is None:
            max_articles = self.max_articles_per_query
        
        try:
            region = aws_config['body']['region']
            arn = aws_config['body']['arn']
            
            if region not in self.aws_clients or not arn:
                return []
            
            # Load actual cookies from cookie file (using cache)
            if 'file' in cookies:
                cookie_dict = self.load_cookies_from_file(cookies['file'], self.scraper_name)
            else:
                cookie_dict = {}
            
            aws_client = self.aws_clients[region]
            all_articles = []
            
            # Calculate pagination parameters
            max_pages = min(self.max_pages_per_query, max(1, max_articles // self.items_per_page))
            if max_articles % self.items_per_page > 0:
                max_pages += 1
            
            for page_num in range(max_pages):
                try:
                    # Create Lambda payload for pagination
                    start_index = page_num * self.items_per_page
                    payload = {
                        "action": "scrape",
                        "scraper_type": self.scraper_name,
                        "query": query,
                        "start": start_index,
                        "count": self.items_per_page,
                        "cookies": cookie_dict,
                        "headers": headers,
                        "mode": mode
                    }
                    
                    # Call Lambda function
                    response = aws_client.invoke_function(arn, payload)
                    
                    if response and response.get('statusCode') == 200:
                        response_body = response.get('body', '{}')
                        if isinstance(response_body, str):
                            response_data = json.loads(response_body)
                        else:
                            response_data = response_body
                        
                        html_content = response_data.get('html_content', '')
                        if html_content:
                            # Extract user agent environment information
                            user_agent_str = headers.get('User-Agent', '')
                            user_agent = self._extract_user_agent_env(user_agent_str)
                            
                            # Parse HTML through parser
                            page_articles = self.parser.parse_search_results(html_content, query, perspective, user_agent)
                            
                            # Add topic information to each article
                            if topic:
                                for article in page_articles:
                                    article['topic'] = topic
                            
                            if page_articles:
                                all_articles.extend(page_articles)
                                
                                # Output page-level results
                                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                page_results = len(page_articles)
                                total_results = len(all_articles)
                                
                                # Console output (including distinguishing value)
                                if distinguishing_value:
                                    print(f"  {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | {distinguishing_value} | Page {page_num + 1} | {page_results} collected | Total {total_results}")
                                    # Log output
                                    logging.info(f"SCRAPING_PROGRESS: {current_time}|{arn}|{self.scraper_name}|{mode}|{query}|{distinguishing_value}|{page_num + 1}|{page_results}|{total_results}")
                                else:
                                    print(f"  {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | Page {page_num + 1} | {page_results} collected | Total {total_results}")
                                    # Log output
                                    logging.info(f"SCRAPING_PROGRESS: {current_time}|{arn}|{self.scraper_name}|{mode}|{query}|{page_num + 1}|{page_results}|{total_results}")
                                
                                # Stop when target article count is reached
                                if len(all_articles) >= max_articles:
                                    # print(f"  Target article count achieved: {len(all_articles)}/{max_articles}")
                                    break
                            else:
                                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                if distinguishing_value:
                                    print(f"  WARNING: {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | {distinguishing_value} | Page {page_num + 1} | 0 collected | Total {len(all_articles)}")
                                else:
                                    print(f"  WARNING: {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | Page {page_num + 1} | 0 collected | Total {len(all_articles)}")
                                logging.warning(f"|{current_time}|{arn}|{self.scraper_name}|{mode}|{query}|{distinguishing_value}| {cookie_dict} | {headers} |No articles found, stopping pagination")
                                break
                        else:
                            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if distinguishing_value:
                                print(f"  ERROR: {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | {distinguishing_value} | Page {page_num + 1} | Response error | Total {len(all_articles)}")
                            else:
                                print(f"  ERROR: {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | Page {page_num + 1} | Response error | Total {len(all_articles)}")
                            logging.error(f"|{current_time}|{arn}|{self.scraper_name}|{mode}|{query}|{distinguishing_value}|{page_num + 1}|{response}|{len(all_articles)}|AWS Lambda returned error")
                            break
                        
                        # Delay between pages (to avoid bot detection)
                        if page_num < max_pages - 1:
                            random_sleep(min_seconds=60, max_seconds=90)
                            
                    except Exception as e:
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"  ERROR: {current_time} | {arn} | {self.scraper_name} | {mode} | {query} | Page {page_num + 1} | Exception occurred | Total {len(all_articles)}")
                        logging.error(f"|{current_time}|{arn}|{self.scraper_name}|{mode}|{query}|{distinguishing_value}|{page_num + 1}|{str(e)}|{len(all_articles)}|Error during AWS Lambda call")
                        continue
                
                # Final result output
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # print(f"  [{current_time}] Pagination complete: {query} | Total {len(all_articles)} articles collected")
                # logging.info(f"Total {len(all_articles)} articles collected for query '{query}' with perspective '{perspective}'")
                return all_articles[:max_articles]  # Return exact count only
                
            except Exception as e:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"  ERROR: [{current_time}] Scraping failed: {arn} | {query} | Error: {str(e)}")
                logging.error(f"AWS Lambda scraping failed for query {arn} | {query}: {str(e)}")  
                return []
    
    def sequential_scraping(self, topics: List[str], queries: Dict[str, Dict[str, List[str]]], 
                           configs: Dict[str, List], save_callback=None, mode: str = None, metadata_list: List[str] = None) -> List[Dict[str, Any]]:
        """Sequential processing by query, parallel processing by perspective within query (real-time save support)"""
        all_articles = []
        cookies_list = configs['cookies']
        headers_list = configs['headers']
        aws_list = configs['aws']
        
        # Setup AWS clients
        self.setup_aws_clients(aws_list)
        
        # Fixed to region mode
        if mode is None:
            mode = 'region'
        
        print(f"\nScraping start - processing {len(topics)} topics total")
        print(f"Mode: region mode (6 parallel)")
        
        for topic_idx, topic in enumerate(topics):
            print(f"\n[{topic_idx+1}/{len(topics)}] Processing: {topic}")
            topic_queries = queries[topic]
            
            # region mode: parallel processing with all 6 configurations
            articles = self._scrape_topic_with_parallel_configs(
                topic, topic_queries, cookies_list, headers_list, aws_list, save_callback, mode, metadata_list
            )
            
            all_articles.extend(articles)
            # print(f"  {topic} complete: {len(articles)} articles collected")
            
            # Delay between each query (to avoid bot detection)
            if topic_idx < len(topics) - 1:  # Only delay if not the last one
                print(f"  Waiting for next query...")
                random_sleep(min_seconds=3, max_seconds=7)
        
        # print(f"\nScraping complete - total {len(all_articles)} articles collected")
        return all_articles
    
    def _scrape_topic_with_parallel_configs(self, topic: str, topic_queries: Dict[str, List[str]], 
                                          cookies_list: List, headers_list: List, aws_list: List, save_callback, mode: str, metadata_list: List = None) -> List[Dict[str, Any]]:
        """Normal mode: parallel processing with all 6 configurations"""
        all_articles = []
        
        print(f"  Parallel processing: {len(cookies_list)} configurations")
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_config = {}
            
            for i in range(len(cookies_list)):
                cookie_config = cookies_list[i]
                header_config = headers_list[i]
                aws_config = aws_list[i]
                
                # Use all queries within the perspective (usually 1 for region mode)
                for perspective, queries in topic_queries.items():
                    for query in queries:
                        # Determine distinguishing value based on mode
                        if mode == 'region' and metadata_list:
                            # region mode: use region name as distinguishing value
                            region_idx = i % len(metadata_list)
                            distinguishing_value = metadata_list[region_idx]
                        else:
                            distinguishing_value = f"config_{i+1}"
                        
                        future = executor.submit(
                            self.scrape_with_aws_lambda,
                            query=query,
                            perspective=perspective,
                            aws_config=aws_config,
                            cookies=cookie_config['body'],
                            headers=header_config['body'],
                            mode="news",
                            max_articles=50,
                            topic=topic,
                            distinguishing_value=distinguishing_value
                        )
                        future_to_config[future] = {
                            'config_idx': i,
                            'query': query,
                            'perspective': perspective,
                            'distinguishing_value': distinguishing_value
                        }
            
            # Collect results
            for future in as_completed(future_to_config):
                config_info = future_to_config[future]
                try:
                    articles = future.result()
                    if articles:
                        # Add perspective information to articles
                        for article in articles:
                            article['perspective'] = config_info['perspective']
                        
                        all_articles.extend(articles)
                        
                        # Real-time save: save immediately after each config completion
                        if save_callback and articles:
                            distinguishing_value = config_info['distinguishing_value']
                            save_callback(articles, topic, distinguishing_value)
                        
                        print(f"    Config {config_info['config_idx']+1} ({config_info['distinguishing_value']}): {len(articles)} articles")
                    else:
                        print(f"    Config {config_info['config_idx']+1} ({config_info['distinguishing_value']}): 0 articles")
                        
                except Exception as e:
                    print(f"    ERROR: Config {config_info['config_idx']+1} ({config_info['distinguishing_value']}): error - {str(e)}")
                    logging.error(f"Error in parallel config {config_info['config_idx']+1}: {str(e)}")
        
        return all_articles

    def _extract_user_agent_env(self, user_agent_str: str) -> str:
        """Extract environment information from User-Agent string"""
        if not user_agent_str:
            return 'unknown'
        
        user_agent_lower = user_agent_str.lower()
        
        # Extract browser information
        if 'chrome' in user_agent_lower:
            browser = 'Chrome'
        elif 'firefox' in user_agent_lower:
            browser = 'Firefox'
        elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
            browser = 'Safari'
        elif 'edge' in user_agent_lower:
            browser = 'Edge'
        else:
            browser = 'Other'
        
        # Extract OS information
        if 'windows' in user_agent_lower:
            os_name = 'Windows'
        elif 'macintosh' in user_agent_lower or 'mac os' in user_agent_lower:
            os_name = 'macOS'
        elif 'android' in user_agent_lower:
            os_name = 'Android'
        elif 'iphone' in user_agent_lower:
            os_name = 'iPhone'
        elif 'linux' in user_agent_lower:
            os_name = 'Linux'
        else:
            os_name = 'Other'
        
        return f"{browser}-{os_name}"

 

