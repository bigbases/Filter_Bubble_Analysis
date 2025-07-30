"""
Google News Parser
Parses news search results from Google search engine
"""

import re
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from .base_parser import BaseParser


class GoogleNewsParser(BaseParser):
    """Google News search result parser"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.google.com"
    
    def parse_search_results(self, html_content: str, query: str, perspective: str = "", user_agent: str = "") -> List[Dict[str, Any]]:
        """Parse Google News search results"""
        articles = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            # Check mobile environment
            is_mobile = 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent
            
            # Find result container based on environment
            if is_mobile:
                news_items = soup.find_all('article') or soup.find_all('div', class_='xrnccd')
            else:
                news_items = soup.find_all('article') or soup.find_all('div', class_='xrnccd') or soup.find_all('div', class_='SoaBEf')
            
            for i, item in enumerate(news_items[:20]):  # Limit to 20 results
                try:
                    # Source extraction (newspaper name)
                    source_elem = item.find('div', class_='CEMjEf') or item.find('span', class_='vr1PYe')
                    source = self.safe_extract_text(source_elem) if source_elem else "Unknown Source"
                    
                    # Title extraction (different selectors for mobile/desktop)
                    title_elem = item.find('h3') or \
                               item.find('a', class_='JtKRv') or \
                               item.find('div', class_='mCBkyc')
                    title = self.safe_extract_text(title_elem) if title_elem else ""
                    
                    # Content extraction (snippet)
                    content_elem = item.find('div', class_='GI74Re') or item.find('span', class_='Y3v8qd')
                    content = self.safe_extract_text(content_elem) if content_elem else ""
                    
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
                        'scraper': 'google_news',
                        'position': i + 1,  # Search result ranking
                        'user_agent': user_agent  # For debugging
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logging.warning(f"Error parsing Google news item {i}: {str(e)}")
                    continue
            
            # Output parsing results as a single delimiter log
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"PARSING_COMPLETE: {current_time}|google_news|{query}|{perspective}|{len(articles)}|{user_agent}")
            
        except Exception as e:
            logging.error(f"Error parsing Google News results: {str(e)}")
        
        return articles
    
    def get_search_url(self, mode: str = "news") -> str:
        """Get Google search URL"""
        # Google uses same URL for all modes
        return "https://www.google.com/search"
    
    def get_search_params(self, query: str, mode: str = "news", page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """Get Google search parameters"""
        params = {
            'q': query,
        }
        
        # Add mode-specific parameters
        if mode == "search_history":
            # Search history accumulation mode parameters
            params.update({
                'hl': 'en',
                'gl': 'us'
            })
        else:
            # News search mode parameters
            params.update({
                'tbm': 'nws'  # News search
            })
        
        # Add pagination parameters
        if page_num > 0:
            params['start'] = page_num * items_per_page
        
        return params
    
    def get_base_search_params(self, query: str) -> Dict[str, Any]:
        """Get base search parameters"""
        return {
            'q': query,
        }
    
    def get_mode_specific_params(self, mode: str = "news") -> Dict[str, Any]:
        """Get mode-specific parameters"""
        if mode == "search_history":
            return {
                'hl': 'en',
                'gl': 'us'
            }
        else:
            return {
                'tbm': 'nws'
            }
    
    def get_pagination_params(self, page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """Get pagination parameters"""
        params = {}
        
        # Pagination (Google uses start parameter)
        if page_num > 0:
            params['start'] = page_num * items_per_page
        
        return params
    
    def build_final_params(self, query: str, mode: str = "news", page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """Build final parameters"""
        base_params = self.get_base_search_params(query)
        mode_params = self.get_mode_specific_params(mode)
        pagination_params = self.get_pagination_params(page_num, items_per_page)
        
        # Merge all parameters
        final_params = {**base_params, **mode_params, **pagination_params}
        
        # Apply pagination based on page number
        if page_num > 0:
            # First page has no start parameter
            if page_num == 1:
                final_params['start'] = items_per_page
            else:
                # Second page onwards add start parameter
                # page_num=1 means start=10 (10-20th results)
                # page_num=2 means start=20 (20-30th results)
                final_params['start'] = page_num * items_per_page
        
        return final_params 