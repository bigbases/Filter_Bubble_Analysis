import json
import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional


class ConfigManager:
    """Configuration file management class"""
    
    def __init__(self, scraper_name: str, mode: str):
        self.scraper_name = scraper_name
        self.mode = mode
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(self.current_dir, '..', 'config', scraper_name)
        self.base_config_dir = os.path.join(self.current_dir, '..', 'config')
        
    def load_json(self, file_name: str) -> Dict[str, Any]:
        """Load JSON file"""
        file_path = os.path.join(self.config_dir, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Config file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file {file_path}: {str(e)}")
            raise
    
    def load_topics(self) -> List[str]:
        """Load topic list"""
        topic_file_path = os.path.join(self.base_config_dir, 'topic.csv')
        try:
            df = pd.read_csv(topic_file_path)
            return df['query'].tolist()
        except FileNotFoundError:
            logging.error(f"Topic file not found: {topic_file_path}")
            raise
        except KeyError:
            logging.error("'query' column not found in topic.csv")
            raise
    
    def load_search_history(self) -> Dict[str, Dict[str, List[str]]]:
        """Search history loading feature removed (region mode only)"""
        logging.warning("Search history feature has been removed. Only region mode is supported.")
        return {}
    
    def load_aws_config(self, region: str = 'us-west-1') -> List[Dict[str, Any]]:
        """Load AWS configuration"""
        aws_config_path = os.path.join(self.current_dir, '..', 'aws', 'aws_functions.json')
        try:
            with open(aws_config_path, 'r', encoding='utf-8') as f:
                aws_config = json.load(f)
            return aws_config.get(region, [])
        except FileNotFoundError:
            logging.error(f"AWS config file not found: {aws_config_path}")
            raise
    
    def get_cookies_by_mode(self) -> List[Dict[str, Any]]:
        """Return cookies configuration list for region mode"""
        cookies_config = self.load_json('cookies.json')
        
        # region mode: replicate default to 6 items
        if 'default' in cookies_config:
            default_cookie = cookies_config['default']
            result = []
            for i in range(6):
                result.append({
                    "name": f"default_{i+1}",
                    "body": default_cookie.copy()
                })
            return result
        else:
            # if no default, replicate first value to 6 items
            if cookies_config:
                first_key = list(cookies_config.keys())[0]
                first_value = cookies_config[first_key]
                result = []
                for i in range(6):
                    result.append({
                        "name": f"{first_key}_{i+1}",
                        "body": first_value.copy()
                    })
                return result
            else:
                result = []
                for i in range(6):
                    result.append({
                        "name": f"empty_{i+1}",
                        "body": {}
                    })
                return result
    
    def get_headers_by_mode(self) -> List[Dict[str, Any]]:
        """Return headers configuration list for region mode"""
        headers_config = self.load_json('headers.json')
        if 'default' in headers_config:
            default_header = headers_config['default']
            result = []
            for i in range(6):
                result.append({
                    "name": f"default_{i+1}",
                    "body": default_header.copy()
                })
            return result
        else:
            if headers_config:
                first_key = list(headers_config.keys())[0]
                first_value = headers_config[first_key]
                result = []
                for i in range(6):
                    result.append({
                        "name": f"{first_key}_{i+1}",
                        "body": first_value.copy()
                    })
                return result
            else:
                result = []
                for i in range(6):
                    result.append({
                        "name": f"empty_{i+1}",
                        "body": {}
                    })
                return result
    
    def get_aws_config_by_mode(self) -> List[Dict[str, Any]]:
        """Return AWS configuration list for region mode (always 6 items)"""
        aws_config_path = os.path.join(self.current_dir, '..', 'aws', 'aws_functions.json')
        try:
            with open(aws_config_path, 'r', encoding='utf-8') as f:
                aws_config = json.load(f)
        except FileNotFoundError:
            logging.error(f"AWS config file not found: {aws_config_path}")
            raise
        
        # region mode: get one from each region to make 6 items
        result = []
        for region, configs in aws_config.items():
            if configs and len(result) < 6:  # up to 6 items only
                result.append({
                    "name": region,
                    "body": configs[0]
                })
        
        # if less than 6, fill the shortage from us-west-1
        if len(result) < 6:
            us_west_configs = aws_config.get('us-west-1', [])
            needed = 6 - len(result)
            for i in range(needed):
                if i < len(us_west_configs):
                    result.append({
                        "name": f"us-west-1_extra_{i+1}",
                        "body": us_west_configs[i]
                    })
        
        # if still less than 6, repeat last configuration to make 6 items
        if len(result) < 6 and result:
            last_config = result[-1]["body"]
            while len(result) < 6:
                result.append({
                    "name": f"duplicate_{len(result)}",
                    "body": last_config.copy()
                })
        
        return result[:6]  # return exactly 6 items
    
    def get_config_by_mode(self) -> Dict[str, List]:
        """Return all configurations by mode as dict format (AWS always 6 items)"""
        return {
            'cookies': self.get_cookies_by_mode(),
            'headers': self.get_headers_by_mode(),
            'aws': self.get_aws_config_by_mode()
        }
