"""
Base parser class for search engines
All search engine parsers should inherit from this base class
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import json


class BaseParser(ABC):
    """Search engine parser base class"""
    
    def __init__(self):
        pass
    
    @abstractmethod
    def parse_search_results(self, html_content: str, query: str, perspective: str = "", user_agent: str = "") -> List[Dict[str, Any]]:
        """
        Parse search results from HTML content
        
        Args:
            html_content: HTML content to parse
            query: Search query
            perspective: Search perspective (support/oppose/default)
            user_agent: User agent information
            
        Returns:
            List of article dictionaries
        """
        pass
    
    @abstractmethod
    def get_search_url(self, mode: str = "news") -> str:
        """
        Get search URL for the search engine
        
        Args:
            mode: Search mode ("news", "search_history", etc.)
            
        Returns:
            Search URL string
        """
        pass
    
    @abstractmethod
    def get_search_params(self, query: str, mode: str = "news", page_num: int = 0, items_per_page: int = 10) -> Dict[str, Any]:
        """
        Get search parameters for the search engine
        
        Args:
            query: Search query
            mode: Search mode
            page_num: Page number (0-based)
            items_per_page: Number of items per page
            
        Returns:
            Dictionary of search parameters
        """
        pass
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might cause issues
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    def safe_extract_text(self, element) -> str:
        """Safe text extraction"""
        if element and hasattr(element, 'get_text'):
            return self.clean_text(element.get_text())
        return ""
    
    def safe_extract_attr(self, element, attr: str) -> str:
        """Safe attribute extraction"""
        if element and hasattr(element, 'get') and element.get(attr):
            return element.get(attr)
        return "" 