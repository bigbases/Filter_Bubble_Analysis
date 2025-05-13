import bing_news.create_acceptlanguage 
import bing_news.create_useragent
import bing_news.create_region
import bing_news.create_searchhistory

import bing_search.create_acceptlanguage 
import bing_search.create_useragent
import bing_search.create_region
import bing_search.create_searchhistory


import google_news.create_acceptlanguage 
import google_news.create_useragent
import google_news.create_region
import google_news.create_searchhistory

import google_search.create_acceptlanguage 
import google_search.create_useragent
import google_search.create_region
import google_search.create_searchhistory

import threading
import logging
import time 
import schedule

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Set up logging to file
logging.basicConfig(filename='./log.txt', filemode='a', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_service(service, created_date):
    logging.info(f"Starting data generation for {service.__name__}")
    try:
        service.create_acceptlanguage.start(created_date)
        service.create_useragent.start(created_date)
        service.create_region.start(created_date)
        service.create_searchhistory.start(created_date)
        logging.info(f"Completed data generation for {service.__name__}")
    except Exception as e:
        logging.error(f"Error in data generation for {service.__name__}: {e}")

def run_all_services(created_date):
    # services = [bing_news, google_news]
    services = [google_news]
    threads = []
    
    for service in services:
        thread = threading.Thread(target=run_service, args=(service, created_date))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

def job():
    logging.info("Starting scheduled job")
    created_date = time.strftime("%Y-%m-%d")
    run_all_services(created_date)
    logging.info("Completed scheduled job")

# Schedule the job to run daily at 3 AM
schedule.every().day.at("14:18").do(job)

if __name__ == "__main__":
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # wait one minute
    except KeyboardInterrupt:
        logging.info("Script interrupted by user")
        print("Script execution has been stopped by user.")