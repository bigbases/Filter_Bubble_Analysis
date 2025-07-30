import json
import pandas as pd
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


class DataProcessor:
    """Data processing and storage class"""
    
    def __init__(self, scraper_name: str = 'bing_news', mode: str = 'region', 
                 base_dir: str = 'datasets'):
        self.scraper_name = scraper_name
        self.mode = mode
        self.base_dir = base_dir
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        self.output_dir = self._create_output_directory()
        
    def _create_output_directory(self) -> str:
        """Create new folder structure: datasets/date/search_engine/mode/"""
        output_path = os.path.join(
            self.base_dir,
            self.date_str,
            self.scraper_name,
            self.mode
        )
        
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)
            logging.info(f"Created output directory: {output_path}")
        
        return output_path
    
    def generate_filename(self, topic: str, metadata: str) -> str:
        """Generate filename by mode
        
        Args:
            topic: topic name
            metadata: additional information by mode (region name, perspective-count, language code, environment name)
        
        Returns:
            str: filename (without extension)
        """
        # Convert special characters to safe characters
        safe_topic = topic.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe_metadata = metadata.replace('/', '_').replace('\\', '_').replace(':', '_')
        
        return f"{safe_topic}_{safe_metadata}"
        
    def ensure_output_directory(self):
        """Create output directory (maintained for backward compatibility)"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_articles(self, articles: List[Dict[str, Any]]) -> pd.DataFrame:
        """Process article data"""
        if not articles:
            return pd.DataFrame()
        
        # Basic data cleaning
        processed_data = []
        for article in articles:
            processed_article = {
                'title': self.clean_text(article.get('title', '')),
                'url': article.get('url', ''),
                'snippet': self.clean_text(article.get('snippet', '')),
                'source': self.clean_text(article.get('source', '')),
                'query': article.get('query', ''),
                'topic': article.get('topic', article.get('query', '')),  # Add topic information
                'perspective': article.get('perspective', ''),
                'scraper': article.get('scraper', ''),
                'timestamp': article.get('timestamp', time.time()),
                'date_collected': datetime.fromtimestamp(
                    article.get('timestamp', time.time())
                ).strftime('%Y-%m-%d %H:%M:%S')
            }
            processed_data.append(processed_article)
        
        df = pd.DataFrame(processed_data)
        
        # Remove duplicates (based on URL)
        df = df.drop_duplicates(subset=['url'], keep='first')
        
        # Remove empty titles or URLs
        df = df[df['title'].str.strip() != '']
        df = df[df['url'].str.strip() != '']
        
        logging.info(f"Processed {len(df)} unique articles")
        return df
    
    def clean_text(self, text: str) -> str:
        """Clean text"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        
        # Combine multiple spaces into one
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        return text
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """Save to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_data_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            df.to_csv(filepath, index=False, encoding='utf-8')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"FILE_SAVED: {timestamp}|{self.scraper_name}|{self.mode}|CSV|{len(df)} rows|{filename}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to save CSV: {str(e)}")
            raise
    
    def save_to_json(self, articles: List[Dict[str, Any]], filename: str = None) -> str:
        """Save to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_data_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"FILE_SAVED: {timestamp}|{self.scraper_name}|{self.mode}|JSON|{len(articles)} items|{filename}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to save JSON: {str(e)}")
            raise
    
    def save_topic_data(self, articles: List[Dict[str, Any]], topic: str, 
                       metadata: str, save_format: str = 'csv') -> Dict[str, str]:
        """Save topic-specific data
        
        Args:
            articles: article data
            topic: topic name
            metadata: mode-specific metadata (region name, perspective-count, language code, environment name)
            save_format: save format ('csv', 'json', 'both')
        
        Returns:
            Dict[str, str]: saved file paths
        """
        results = {}
        
        if not articles:
            logging.warning(f"No articles to save for topic: {topic}")
            return results
        
        # Process data
        df = self.process_articles(articles)
        
        if df.empty:
            logging.warning(f"No processed articles for topic: {topic}")
            return results
        
        # Generate filename
        base_filename = self.generate_filename(topic, metadata)
        
        # Save
        if save_format in ['csv', 'both']:
            csv_filename = f"{base_filename}.csv"
            csv_file = self.save_to_csv(df, csv_filename)
            results['csv'] = csv_file
        
        if save_format in ['json', 'both']:
            json_filename = f"{base_filename}.json"
            json_file = self.save_to_json(articles, json_filename)
            results['json'] = json_file
        
        return results
    
    def create_summary_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create collection summary report"""
        if df.empty:
            return {"error": "No data to summarize"}
        
        summary = {
            "total_articles": len(df),
            "unique_sources": df['source'].nunique(),
            "queries_processed": df['query'].nunique(),
            "perspectives": df['perspective'].value_counts().to_dict(),
            "sources": df['source'].value_counts().head(10).to_dict(),
            "queries": df['query'].value_counts().to_dict(),
            "date_range": {
                "start": df['date_collected'].min(),
                "end": df['date_collected'].max()
            },
            "scrapers_used": df['scraper'].value_counts().to_dict(),
            "scraper_name": self.scraper_name,
            "mode": self.mode,
            "date": self.date_str
        }
        
        return summary
    
    def save_summary_report(self, summary: Dict[str, Any], filename: str = None) -> str:
        """Save summary report"""
        if filename is None:
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"summary_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            logging.info(f"Summary report saved to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to save summary: {str(e)}")
            raise
    
    def process_and_save(self, articles: List[Dict[str, Any]], 
                        save_format: str = 'both') -> Dict[str, str]:
        """Full processing and saving pipeline (maintained for backward compatibility)"""
        results = {}
        
        # Process data
        df = self.process_articles(articles)
        
        if df.empty:
            logging.warning("No articles to process")
            return results
        
        # Save
        timestamp = datetime.now().strftime('%H%M%S')
        
        if save_format in ['csv', 'both']:
            csv_file = self.save_to_csv(df, f"news_data_{timestamp}.csv")
            results['csv'] = csv_file
        
        if save_format in ['json', 'both']:
            json_file = self.save_to_json(articles, f"news_data_{timestamp}.json")
            results['json'] = json_file
        
        # Summary report
        summary = self.create_summary_report(df)
        summary_file = self.save_summary_report(summary, f"summary_{timestamp}.json")
        results['summary'] = summary_file
        
        # Print summary to console
        self.print_summary(summary)
        
        return results
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print summary to console"""
        print("\n" + "="*50)
        print("Data Collection Complete Summary")
        print("="*50)
        print(f"Total articles: {summary.get('total_articles', 0)}")
        print(f"Unique sources: {summary.get('unique_sources', 0)}")
        print(f"Processed queries: {summary.get('queries_processed', 0)}")
        
        if summary.get('perspectives'):
            print("\nPerspective Distribution:")
            for perspective, count in summary['perspectives'].items():
                print(f"  {perspective}: {count} items")
        
        if summary.get('sources'):
            print("\nTop Sources (top 5):")
            for source, count in list(summary['sources'].items())[:5]:
                print(f"  {source}: {count} items")
        
        print(f"\nCollection Period: {summary.get('date_range', {}).get('start', 'N/A')} ~ {summary.get('date_range', {}).get('end', 'N/A')}")
        print(f"Scraper: {summary.get('scraper_name', 'N/A')}")
        print(f"Mode: {summary.get('mode', 'N/A')}")
        print(f"Saved Folder: {self.output_dir}")
        print("="*50)
