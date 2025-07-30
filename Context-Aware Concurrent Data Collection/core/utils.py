import logging
import time
import random
import os
import glob
from functools import wraps
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler


def get_log_stats(logs_dir='logs'):
    """Log directory statistics information"""
    if not os.path.exists(logs_dir):
        return {"total_files": 0, "total_size": 0}
    
    log_files = glob.glob(os.path.join(logs_dir, '*.log'))
    total_size = sum(os.path.getsize(f) for f in log_files)
    
    return {
        "total_files": len(log_files),
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }


def cleanup_old_logs(logs_dir='logs', days_to_keep=7):
    """Clean up old log files"""
    if not os.path.exists(logs_dir):
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    log_files = glob.glob(os.path.join(logs_dir, '*.log*'))
    
    cleaned_count = 0
    cleaned_size = 0
    
    for log_file in log_files:
        try:
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            
            if file_modified_time < cutoff_date:
                file_size = os.path.getsize(log_file)
                os.remove(log_file)
                cleaned_count += 1
                cleaned_size += file_size
                
        except Exception as e:
            logging.warning(f"Failed to clean log file {log_file}: {str(e)}")
    
    if cleaned_count > 0:
        cleaned_mb = round(cleaned_size / (1024 * 1024), 2)
        print(f"{cleaned_count} files cleaned ({cleaned_mb}MB saved)")


def setup_logging(scraper_name='scraper', mode='default', level=logging.INFO):
    """Set up date-based logging (with rotation)"""
    # Create logs directory
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    # Print existing log statistics
    stats = get_log_stats(logs_dir)
    if stats["total_files"] > 0:
        print(f"Existing logs: {stats['total_files']} files, {stats['total_size_mb']}MB")
    
    # Clean up old log files (files older than 7 days)
    cleanup_old_logs(logs_dir, days_to_keep=7)
    
    # Generate date-based log filename
    date_str = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%H%M%S')
    log_filename = f"{date_str}_{scraper_name}_{mode}_{time_str}.log"
    log_file_path = os.path.join(logs_dir, log_filename)
    
    # Remove existing handlers (prevent duplication)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Set up rotating file handler (file size limit: 10MB, max 5 backups)
    file_handler = RotatingFileHandler(
        log_file_path, 
        mode='a', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Set up console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Configure logger
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler]
    )
    
    logging.info(f"Log system initialization completed")
    logging.info(f"Log file: {log_file_path}")
    
    return log_file_path


def retry_on_failure(max_retries=3, delay=1):
    """Retry decorator for functions that may fail"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logging.error(f"Function {func.__name__} failed after {max_retries} attempts: {str(e)}")
                        raise
                    else:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay} seconds...")
                        time.sleep(delay)
            return None
        return wrapper
    return decorator


def random_sleep(min_seconds=1, max_seconds=3):
    """Random sleep to avoid bot detection"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)


def ensure_directory_exists(directory_path):
    """Create directory if it doesn't exist"""
    os.makedirs(directory_path, exist_ok=True)


def safe_text_extract(element, default=""):
    """Safe text extraction (for BeautifulSoup elements)"""
    if element:
        return element.get_text(strip=True)
    return default


def safe_attr_extract(element, attr, default=""):
    """Safe attribute extraction (for BeautifulSoup elements)"""
    if element and element.has_attr(attr):
        return element[attr]
    return default


def format_log_message(topic="", perspective="", count=0, extra_info=""):
    """Format log message consistently"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"{timestamp}|{topic}|{perspective}|{count}|{extra_info}"


def validate_data_structure(data, required_fields):
    """Data structure validation"""
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data:
            return False
    
    return True


def chunk_list(lst, chunk_size):
    """Split list into n-sized chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_filename(filename):
    """Convert unsafe characters to safe characters for filename"""
    import re
    # Replace unsafe characters with underscores
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    return safe_name 