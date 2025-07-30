"""
Parser module
Provides classes for parsing results from various search engines
"""

from .base_parser import BaseParser
from .bing_news_parser import BingNewsParser

__all__ = ['BaseParser', 'BingNewsParser'] 