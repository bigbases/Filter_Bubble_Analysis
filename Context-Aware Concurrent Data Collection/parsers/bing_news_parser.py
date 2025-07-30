"""
Bing News Parser
Parses news search results from Bing search engine
"""

import re
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from .base_parser import BaseParser


class BingNewsParser(BaseParser):
    """Bing News search result parser"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.bing.com"
    
    def parse_search_results(self, html_content: str, query: str, perspective: str = "", user_agent: str = "") -> List[Dict[str, Any]]:
        """Parse Bing News search results"""
        articles = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            # Check mobile environment
            is_mobile = 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent
            
            # Find result container based on environment
            if is_mobile:
                # Mobile environment selectors
                news_items = soup.find_all('div', class_='newsitem') or \
                           soup.find_all('div', class_='news-card') or \
                           soup.find_all('div', {'data-tag': 'news'})
            else:
                # Try different patterns
                news_items = soup.find_all('div', class_='newsitem') or \
                           soup.find_all('div', class_='news-card') or \
                           soup.find_all('article') or \
                           soup.find_all('div', {'data-tag': 'news'}) or \
                           soup.find_all('li', class_='b_algo') or \
                           soup.find_all('div', class_='b_algo')
            
            for i, item in enumerate(news_items[:20]):  # Limit to 20 results
                try:
                    if is_mobile:
                        # Mobile environment: extract limited information only
                        source = "Unknown Source"  # Mobile doesn't have source info
                        content = ""  # Mobile doesn't have content info
                        
                        # Title extraction
                        title_elem = item.find('a') or item.find('h2') or item.find('h3')
                        title = self.safe_extract_text(title_elem) if title_elem else ""
                        
                        # URL extraction
                        url_elem = item.find('a')
                        url = ""
                        if url_elem and url_elem.get('href'):
                            url = urljoin(self.base_url, url_elem.get('href'))
                    
                    else:
                        # Desktop environment: extract full information
                        # Source extraction (newspaper name)
                        source_elem = item.find('span', class_='source') or \
                                    item.find('div', class_='source') or \
                                    item.find('cite') or \
                                    item.find('a', class_='source')
                        source = self.safe_extract_text(source_elem) if source_elem else "Unknown Source"
                        
                        # Content extraction (snippet)
                        content_elem = item.find('p') or \
                                     item.find('div', class_='snippet') or \
                                     item.find('span', class_='snippet')
                        content = self.safe_extract_text(content_elem) if content_elem else ""
                        
                        # Title extraction
                        title_elem = item.find('a') or \
                                   item.find('h2', class_='title') or \
                                   item.find('h3')
                        title = self.safe_extract_text(title_elem) if title_elem else ""
                        
                        # URL extraction
                        url_elem = item.find('a')
                        url = ""
                        if url_elem and url_elem.get('href'):
                            url = urljoin(self.base_url, url_elem.get('href'))
                    
                    # Minimum data validation
                    if not title or not url:
                        continue
                    
                    article = {
                        'title': title,
                        'description': content,
                        'url': url,
                        'published_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': source,
                        'query': query,
                        'perspective': perspective,
                        'scraper': 'bing_news',
                        'position': i + 1,  # Search result ranking
                        'user_agent': user_agent  # For debugging
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logging.warning(f"Error parsing Bing news item {i}: {str(e)}")
                    continue
            
            # Output parsing results as a single delimiter log
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"PARSING_COMPLETE: {current_time}|bing_news|{query}|{perspective}|{len(articles)}|{user_agent}")
            
        except Exception as e:
            logging.error(f"Error parsing Bing News results: {str(e)}")
        
        return articles
    
    def get_search_url(self, mode: str = "news") -> str:
        """Get Bing search URL"""
        if mode == "search_history":
            return "https://www.bing.com/search"
        else:
            return "https://www.bing.com/news/search"
    
    def get_search_params(self, query: str, mode: str = "news", page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """Get Bing search parameters"""
        params = {
            'q': query,
        }
        
        # Add pagination parameters
        if page_num > 0:
            # First page has no first parameter
            if page_num == 1:
                params['first'] = items_per_page
            else:
                # Second page onwards add first parameter
                # page_num=1 means first=10 (10-20th results)
                # page_num=2 means first=20 (20-30th results)
                params['first'] = page_num * items_per_page
        
        return params
    
    def get_base_search_params(self, query: str, mode: str = "news") -> Dict[str, Any]:
        """Get base search parameters by mode"""
        if mode == "search_history":
            # Search history accumulation URL
            return {
                'q': query,
            }
        else:
            # News search URL
            return {
                'q': query,
            }
    
    def get_mode_specific_params(self, mode: str = "news") -> Dict[str, Any]:
        """Get mode-specific parameters"""
        if mode == "search_history":
            # Search history accumulation mode parameters
            return {
                'setmkt': 'en-US',
                'form': 'QBLH'  # Form for search history accumulation
            }
        else:
            # News search mode parameters
            return {
                'setmkt': 'en-US',
                'form': 'HDRSC1'  # Form for news search
            }
    
    def get_pagination_params(self, page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """Get pagination parameters"""
        params = {}
        
        if page_num > 0:
            if page_num == 1:
                params['first'] = items_per_page
            else:
                params['first'] = page_num * items_per_page
        
        return params
    
    def build_final_params(self, query: str, mode: str = "news", page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """Build final parameters by combining base parameters and pagination parameters"""
        base_params = self.get_base_search_params(query, mode)
        mode_params = self.get_mode_specific_params(mode)
        pagination_params = self.get_pagination_params(page_num, items_per_page)
        
        # Merge base parameters and pagination parameters
        final_params = {**base_params, **mode_params, **pagination_params}
        
        return final_params 