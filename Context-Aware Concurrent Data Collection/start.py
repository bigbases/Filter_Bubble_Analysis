from user_context_controller.config import ConfigManager
from core.aws_client import AWSLambdaClient
from core.utils import setup_logging
from context_aware_concurrent_collector.detail_content_scraper import DetailContentScraper
from context_aware_concurrent_collector.data_processor import DataProcessor
import context_aware_concurrent_collector.requester as requester
import logging
import time
import json
from collections import defaultdict
import schedule
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def get_metadata_by_mode(config_manager, mode):
    """Return metadata list by mode
    
    Returns:
        List[str]: Metadata list by mode
    """
    if mode == 'region':
        # AWS region names
        return ['us-west-1', 'us-east-2', 'ap-northeast-1', 'ap-northeast-2', 'eu-west-3', 'eu-west-2']
    else:
        return ['default']


def organize_articles_by_metadata(articles, mode, metadata_list=None):
    """Organize articles by metadata according to mode
    
    Returns:
        Dict[str, Dict[str, List]]: {topic: {metadata: articles}}
    """
    organized = defaultdict(lambda: defaultdict(list))
    
    if mode == 'region':
        # region mode: distribute articles by region
        region_index = 0
        regions = metadata_list or ['us-west-1', 'us-east-2', 'ap-northeast-1', 'ap-northeast-2', 'eu-west-3', 'eu-west-2']
        
        for article in articles:
            topic = article.get('topic', article.get('query', 'unknown'))  # topic first, query if not available
            region = regions[region_index % len(regions)]
            # unify perspective to 'default'
            article['perspective'] = 'default'
            organized[topic][region].append(article)
            region_index += 1
    else:
        # default mode: classify by topic only
        for article in articles:
            topic = article.get('topic', article.get('query', 'unknown'))  # topic first, query if not available
            # unify perspective to 'default'
            article['perspective'] = 'default'
            organized[topic]['default'].append(article)
    
    return dict(organized)


def run_single_scraper(scraper_name, mode, topics):
    """Single scraper execution function (for parallel execution)
    
    Args:
        scraper_name: 'google_news' or 'bing_news'
        mode: execution mode
        topics: list of topics to collect
        
    Returns:
        dict: execution result information
    """
    try:
        print(f"\n[{scraper_name}] {mode} mode start - {datetime.now().strftime('%H:%M:%S')}")
        
        # Initialize configuration manager
        config_manager = ConfigManager(scraper_name, mode=mode)
        
        # Initialize date-based logging setup
        log_file_path = setup_logging(
            scraper_name=scraper_name,
            mode=mode, 
            level=logging.INFO
        )
        
        # Load configuration
        config = config_manager.get_config_by_mode()
        cookies = config['cookies']
        headers = config['headers']
        aws_configs = config['aws']
        
        # Check metadata by mode
        metadata_list = get_metadata_by_mode(config_manager, mode)
        
        # region mode uses basic topics
        queries = {}
        for topic in topics:
            queries[topic] = {'default': [topic]}
        
        # Initialize scraper
        scraper = DetailContentScraper(scraper_name)
        data_processor = DataProcessor(
            scraper_name=scraper_name,
            mode=mode,
            base_dir='datasets'
        )
        
        # 🔥 Real-time save callback function
        def save_callback(articles, topic, metadata):
            """Callback function to save immediately upon completion"""
            if articles:
                try:
                    results = data_processor.save_topic_data(
                        articles=articles,
                        topic=topic,
                        metadata=metadata,
                        save_format='csv'
                    )
                    
                    if results:
                        for format_type, filepath in results.items():
                            logging.info(f"FILE_SAVED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}|{scraper_name}|{mode}|{format_type.upper()}|{len(articles)}|{filepath}")
                
                except Exception as e:
                    logging.error(f"Save callback failed for {topic}_{metadata}: {str(e)}")

        # Execute data collection
        start_time = time.time()
        articles = scraper.sequential_scraping(topics, queries, config, save_callback=save_callback, mode=mode, metadata_list=metadata_list)
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate overall summary report
        summary_file = None
        if articles:
            from pandas import DataFrame
            df = data_processor.process_articles(articles)
            summary = data_processor.create_summary_report(df)
            summary_file = data_processor.save_summary_report(summary)
        
        result = {
            'scraper': scraper_name,
            'mode': mode,
            'articles_count': len(articles),
            'duration': duration,
            'summary_file': summary_file,
            'status': 'success'
        }
        
        print(f"[{scraper_name}] {mode} mode completed - {len(articles)} articles, {duration:.1f} seconds")
        return result
        
    except Exception as e:
        error_msg = f"[{scraper_name}] {mode} mode failed: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        return {
            'scraper': scraper_name,
            'mode': mode,
            'articles_count': 0,
            'duration': 0,
            'summary_file': None,
            'status': 'failed',
            'error': str(e)
        }


def run_mode_parallel(mode, topics):
    """Run Google and Bing in parallel for specific mode
    
    Args:
        mode: execution mode ('region')
        topics: list of topics to collect
        
    Returns:
        list: execution results of each scraper
    """
    print(f"\n=== {mode.upper()} MODE PARALLEL EXECUTION START ===")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Run Google and Bing scrapers in parallel
        future_to_scraper = {
            executor.submit(run_single_scraper, 'google_news', mode, topics): 'google_news',
            executor.submit(run_single_scraper, 'bing_news', mode, topics): 'bing_news'
        }
        
        results = []
        for future in as_completed(future_to_scraper):
            scraper_name = future_to_scraper[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                error_result = {
                    'scraper': scraper_name,
                    'mode': mode,
                    'articles_count': 0,
                    'duration': 0,
                    'summary_file': None,
                    'status': 'failed',
                    'error': str(e)
                }
                results.append(error_result)
                print(f"[{scraper_name}] execution error: {str(e)}")
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Result summary
    print(f"\n=== {mode.upper()} MODE EXECUTION COMPLETED ===")
    print(f"Total time taken: {total_duration:.1f} seconds")
    
    total_articles = 0
    for result in results:
        status_icon = "SUCCESS" if result['status'] == 'success' else "FAILED"
        print(f"{status_icon} {result['scraper']}: {result['articles_count']} articles, {result['duration']:.1f} seconds")
        if result['status'] == 'success':
            total_articles += result['articles_count']
        elif result['status'] == 'failed':
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print(f"Total collected articles: {total_articles}")
    
    return results


def run_all_modes_sequential(topics):
    """Execute region mode sequentially (Google and Bing run in parallel within the mode)
    
    Args:
        topics: list of topics to collect
        
    Returns:
        dict: overall execution result summary
    """
    modes = ['region']
    all_results = []
    
    print(f"\n=== SEQUENTIAL MODE EXECUTION START ===")
    print(f"Execution mode: {', '.join(modes)}")
    print(f"Collection topics: {', '.join(topics)}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    for i, mode in enumerate(modes, 1):
        print(f"\n{'='*60}")
        print(f"Progress: {i}/{len(modes)} - {mode.upper()} MODE")
        print(f"{'='*60}")
        
        mode_results = run_mode_parallel(mode, topics)
        all_results.extend(mode_results)
        
        # Brief wait between modes (for system stability)
        if i < len(modes):
            print(f"Preparing for next mode... (5 second wait)")
            time.sleep(5)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Overall result summary
    print(f"\n=== OVERALL EXECUTION COMPLETED ===")
    print(f"Total time taken: {total_duration:.1f} seconds ({total_duration/3600:.1f} hours)")
    
    # Result summary by mode
    mode_summary = {}
    for mode in modes:
        mode_results = [r for r in all_results if r['mode'] == mode]
        mode_summary[mode] = {
            'total_articles': sum(r['articles_count'] for r in mode_results if r['status'] == 'success'),
            'scrapers': len(mode_results),
            'success_count': len([r for r in mode_results if r['status'] == 'success']),
            'failed_count': len([r for r in mode_results if r['status'] == 'failed'])
        }
    
    print(f"\nResult summary by mode:")
    total_articles = 0
    for mode, summary in mode_summary.items():
        print(f"  {mode.upper()}: {summary['total_articles']} articles, {summary['success_count']}/{summary['scrapers']} success")
        total_articles += summary['total_articles']
    
    print(f"\nTotal collected articles: {total_articles}")
    
    return {
        'total_duration': total_duration,
        'total_articles': total_articles,
        'mode_summary': mode_summary,
        'all_results': all_results,
        'completion_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def scheduled_scraping():
    """Scheduled scraping execution function"""
    print(f"\n=== AUTOMATIC SCHEDULED SCRAPING START ===")
    print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load default topics (using Google News configuration)
        config_manager = ConfigManager('google_news', mode='region')
        topics = config_manager.load_topics()
        
        print(f"Collection topics: {', '.join(topics)}")
        
        # Execute all modes sequentially
        final_results = run_all_modes_sequential(topics)
        
        print(f"\nAutomatic scheduled scraping completed!")
        print(f"Total collected articles: {final_results['total_articles']}")
        print(f"Total time taken: {final_results['total_duration']:.1f} seconds")
        
    except Exception as e:
        error_msg = f"ERROR: Automatic scheduled scraping failed: {str(e)}"
        print(error_msg)
        logging.error(error_msg)


def start_scheduler():
    """Scheduler start function"""
    print(f"\n=== SCHEDULER START ===")
    print(f"Automatic scraping will run daily at 00:01.")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Execute scheduled scraping daily at 00:01
    schedule.every().day.at("00:01").do(scheduled_scraping)
    
    print(f"Schedule registration completed")
    print(f"Scheduler running... (Exit with Ctrl+C)")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check schedule every minute
    except KeyboardInterrupt:
        print(f"\nScheduler terminated")


def main():
    """Main function for testing (single mode execution)"""
    print("Web Scraper v2 Start (Test Mode)")
    print("="*50)
    
    # Initialize configuration manager
    mode = 'region'  # region mode only
    config_manager = ConfigManager('bing_news', mode=mode)  # bing_news -> google_news for change
    
    # Initialize date-based logging setup
    log_file_path = setup_logging(
        scraper_name=config_manager.scraper_name, 
        mode=mode, 
        level=logging.INFO
    )
    print(f"Log file: {log_file_path}")
    
    print(f"Execution mode: {mode}")
    print(f"Scraper: {config_manager.scraper_name}")
    
    # Load configuration
    config = config_manager.get_config_by_mode()
    cookies = config['cookies']
    headers = config['headers']
    aws_configs = config['aws']
    
    print(f"Configuration loaded:")
    print(f"  - Cookie settings: {len(cookies)} items")
    print(f"  - Header settings: {len(headers)} items")
    print(f"  - AWS settings: {len(aws_configs)} items")
    print(f'AWS configuration: {aws_configs}')
    
    # Load topics
    topics = config_manager.load_topics()
    # topics = ['"gun law" OR "gun policy" OR "gun control"']
    topics = ['gun', '"gun law" OR "gun policy" OR "gun control"']


    print(f"Collection topics: {len(topics)} items")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")
    
    # Check metadata by mode
    metadata_list = get_metadata_by_mode(config_manager, mode)
    if metadata_list:
        print(f"\n{mode} mode metadata: {len(metadata_list)} items")
        for i, meta in enumerate(metadata_list, 1):
            print(f"  {i}. {meta}")
    
    # region mode uses basic topics (perspective: 'default')
    queries = {}
    for topic in topics:
        queries[topic] = {'default': [topic]}
    print(f"region mode: {len(topics)} topics used (perspective: default)")
    
    # Initialize scraper
    scraper = DetailContentScraper('bing_news')  # bing_news -> google_news for change
    data_processor = DataProcessor(
        scraper_name=config_manager.scraper_name,
        mode=mode,
        base_dir='datasets'
    )
    
    print(f"\nSave path: {data_processor.output_dir}")
    
    # 🔥 Real-time save callback function
    def save_callback(articles, topic, metadata):
        """Callback function to save immediately upon completion"""
        if articles:
            try:
                results = data_processor.save_topic_data(
                    articles=articles,
                    topic=topic,
                    metadata=metadata,
                    save_format='csv'
                )
                
                if results:
                    for format_type, filepath in results.items():
                        print(f"          {format_type.upper()}: {filepath}")
                
            except Exception as e:
                print(f"          Save failed: {str(e)}")
                logging.error(f"Save callback failed for {topic}_{metadata}: {str(e)}")

    # Data collection common to all modes (real-time save)
    print(f"\nData collection start (real-time save) - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        articles = scraper.sequential_scraping(topics, queries, config, save_callback=save_callback, mode=mode, metadata_list=metadata_list)
        print(f"\nCollection completed: {len(articles)} articles")
        
    except Exception as e:
        logging.error(f"Error occurred during scraping: {str(e)}")
        print(f"Error occurred: {str(e)}")
        return
    
    # Generate only overall summary report (individual files already saved)
    if articles:
        print(f"\nGenerating overall summary report...")
        from pandas import DataFrame
        df = data_processor.process_articles(articles)
        summary = data_processor.create_summary_report(df)
        summary_file = data_processor.save_summary_report(summary)
        
        print(f"\nSummary report: {summary_file}")
        data_processor.print_summary(summary)
    else:
        print("No articles collected.")
    
    print(f"\nProgram terminated - {time.strftime('%Y-%m-%d %H:%M:%S')}")


def test_configurations():
    """Configuration test function (legacy code)"""
    print("\n" + "="*50)
    print("🧪 Configuration Test Mode")
    print("="*50)
    
    config_manager = ConfigManager('bing_news', mode='region')
    
    # Test region mode configuration only
    print("=== Region Mode Configuration Test ===")
    config_manager.mode = 'region'
    print(f"\n--- region mode ---")
    config = config_manager.get_config_by_mode()
    
    print("Cookies:")
    for cookie in config['cookies']:
        print(f"  Name: {cookie['name']}")
        print(f"  Body: {cookie['body']}")
        print()
    
    print("Headers:")
    for header in config['headers']:
        print(f"  Name: {header['name']}")
        print(f"  Body: {header['body']}")
        print()
    
    print("AWS:")
    for aws in config['aws']:
        print(f"  Name: {aws['name']}")
        print(f"  Body: {aws['body']}")
        print()


if __name__ == "__main__":
    # Select execution mode
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_configurations()
        elif sys.argv[1] == 'schedule':
            start_scheduler()
        elif sys.argv[1] == 'all':
            # Execute region mode immediately (for testing)
            config_manager = ConfigManager('google_news', mode='region')
            topics = config_manager.load_topics()
            print(f"Immediate region mode execution (test)")
            run_all_modes_sequential(topics)
        else:
            print("❓ Usage:")
            print("  python start.py          # Default test mode (single scraper)")
            print("  python start.py test     # Configuration test")
            print("  python start.py schedule # Start scheduler (automatic execution daily at 00:01)")
            print("  python start.py all      # Immediate region mode execution (for testing)")
    else:
        main()