# Context-Aware Concurrent Data Collection

A high-performance web scraping system that collects news articles from Google News and Bing News across multiple AWS regions concurrently. The system uses region-based context awareness to gather diverse news perspectives from different geographical locations.

## Features

- **Multi-Source Collection**: Scrapes from both Google News and Bing News
- **Region-Based Context**: Collects data from 6 different AWS regions for geographical diversity
- **Concurrent Processing**: Parallel execution for maximum efficiency
- **Real-time Saving**: Articles are saved immediately as they are collected
- **AWS Lambda Integration**: Serverless scraping to avoid rate limiting and IP blocking
- **Comprehensive Logging**: Detailed logging with automatic cleanup and rotation
- **Data Processing**: Built-in data cleaning, deduplication, and format conversion

## System Requirements

- Python 3.8+
- AWS Account with Lambda functions deployed
- Required Python packages (see `requirements.txt`)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Context-Aware Concurrent Data Collection"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials**
   - Set up your AWS credentials using AWS CLI or environment variables
   - Ensure Lambda functions are deployed in the target regions

## Project Structure

```
Context-Aware Concurrent Data Collection/
├── README.md
├── requirements.txt
├── start.py                    # Main entry point
├── aws/
│   ├── aws_functions.json      # AWS Lambda configuration
│   ├── lambda_function.py      # Lambda function code
│   └── lambda_updater.py       # Lambda deployment tool
├── config/
│   ├── topic.csv              # Topics to scrape
│   ├── google_news/
│   │   ├── cookies.json       # Cookie configuration
│   │   └── headers.json       # HTTP headers
│   └── bing_news/
│       ├── cookies.json
│       └── headers.json
├── core/
│   ├── aws_client.py          # AWS Lambda client
│   └── utils.py               # Utility functions
├── parsers/
│   ├── base_parser.py         # Base parser class
│   ├── google_news_parser.py  # Google News parser
│   └── bing_news_parser.py    # Bing News parser
├── context_aware_concurrent_collector/
│   ├── detail_content_scraper.py  # Main scraping engine
│   ├── data_processor.py          # Data processing and saving
│   └── requester.py               # HTTP request utilities
├── user_context_controller/
│   └── config.py              # Configuration management
└── datasets/                  # Output directory (auto-created)
    └── YYYY-MM-DD/           # Date-based folders
        ├── google_news/
        │   └── region/
        └── bing_news/
            └── region/
```

## Configuration

### Topics Configuration
Edit `config/topic.csv` to specify the topics you want to scrape:
```csv
query
<topic-1>
<topic-2>
<topic-3>
```

### AWS Lambda Configuration
Update `aws/aws_functions.json` with your Lambda function ARNs:
```json
{
  "us-west-1": [
    {
      "region": "us-west-1",
      "arn": "arn:aws:lambda:us-west-1:<account-id>:function:<function-name>"
    }
  ],
  "us-east-2": [
    {
      "region": "us-east-2", 
      "arn": "arn:aws:lambda:us-east-2:<account-id>:function:<function-name>"
    }
  ],
  "ap-northeast-1": [
    {
      "region": "ap-northeast-1",
      "arn": "arn:aws:lambda:ap-northeast-1:<account-id>:function:<function-name>"
    }
  ],
  "ap-northeast-2": [
    {
      "region": "ap-northeast-2",
      "arn": "arn:aws:lambda:ap-northeast-2:<account-id>:function:<function-name>"
    }
  ],
  "eu-west-3": [
    {
      "region": "eu-west-3",
      "arn": "arn:aws:lambda:eu-west-3:<account-id>:function:<function-name>"
    }
  ],
  "eu-west-2": [
    {
      "region": "eu-west-2",
      "arn": "arn:aws:lambda:eu-west-2:<account-id>:function:<function-name>"
    }
  ]
}
```

### HTTP Configuration
Customize cookies and headers in:
- `config/google_news/cookies.json`
- `config/google_news/headers.json`
- `config/bing_news/cookies.json`
- `config/bing_news/headers.json`

## Usage

### Basic Usage
```bash
# Run single test scraper
python start.py

# Test configurations
python start.py test

# Run region mode immediately
python start.py all

# Start scheduled scraper (runs daily at 00:01)
python start.py schedule
```

### Advanced Usage

#### Single Scraper Test
```python
from user_context_controller.config import ConfigManager
from context_aware_concurrent_collector.detail_content_scraper import DetailContentScraper

# Initialize
config_manager = ConfigManager('google_news', mode='region')
scraper = DetailContentScraper('google_news')

# Load configuration
topics = config_manager.load_topics()
config = config_manager.get_config_by_mode()

# Run scraping
articles = scraper.sequential_scraping(topics, queries, config, mode='region')
```

## Output Data Structure

### CSV Format
```csv
title,description,url,published_date,source,query,topic,perspective,scraper,user_agent
"<article-title>","<description>","<article-url>","<date>","<source>","<query>","<topic>","default","google_news","Chrome-Windows"
```

### JSON Format
```json
{
  "title": "<article-title>",
  "description": "<article-description>",
  "url": "<article-url>",
  "published_date": "<date>",
  "source": "<source>",
  "query": "<query>",
  "topic": "<topic>",
  "perspective": "default",
  "scraper": "google_news",
  "user_agent": "Chrome-Windows"
}
```

### Directory Structure
```
datasets/
└── YYYY-MM-DD/
    ├── google_news/
    │   └── region/
    │       ├── <topic>_us-west-1.csv
    │       ├── <topic>_us-east-2.csv
    │       └── ...
    └── bing_news/
        └── region/
            ├── <topic>_ap-northeast-1.csv
            ├── <topic>_ap-northeast-2.csv
            └── ...
```

## Region-Based Collection

The system collects data from 6 AWS regions to ensure geographical diversity:

| Region | Location | Purpose |
|--------|----------|---------|
| us-west-1 | US West Coast | North American perspective |
| us-east-2 | US East Coast | North American perspective |
| ap-northeast-1 | Tokyo | Asian perspective |
| ap-northeast-2 | Seoul | Asian perspective |
| eu-west-3 | Paris | European perspective |
| eu-west-2 | London | European perspective |

## Monitoring and Logging

### Log Files
- Location: `logs/` directory
- Format: `YYYY-MM-DD_scraper_mode_HHMMSS.log`
- Automatic rotation: 10MB max, 5 backup files
- Auto cleanup: Files older than 7 days

### Log Levels
- **INFO**: General operation status
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors
- **DEBUG**: Detailed debugging information

### Progress Monitoring
The system provides real-time progress updates:
```
Scraping start - processing N topics total
Mode: region mode (6 parallel)

[1/N] Processing: <topic>
<timestamp> | <lambda-arn> | <scraper> | news | <topic> | <region> | Page 1 | <count> collected | Total <total>
Config 1 (<region>): <count> articles
Waiting for next query...
```

## Troubleshooting

### Common Issues

1. **AWS Lambda Timeout**
   - Increase Lambda timeout in AWS console
   - Reduce `max_articles_per_query` in code

2. **Rate Limiting**
   - Adjust `random_sleep()` parameters
   - Increase delays between requests

3. **Cookie/Header Issues**
   - Update cookies and headers in config files
   - Use browser developer tools to get fresh values

4. **Memory Issues**
   - Process smaller batches
   - Enable real-time saving to reduce memory usage

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

- **Concurrent Processing**: 6 parallel Lambda executions per topic
- **Real-time Saving**: Immediate file writing to prevent data loss
- **Efficient Pagination**: Smart page limit calculation
- **Memory Management**: Streaming data processing
- **Error Recovery**: Automatic retry with exponential backoff

## Security Considerations

- AWS credentials should be stored securely
- Lambda functions run in isolated environments
- No sensitive data stored in logs
- Rate limiting to respect target websites

## License

This project is for research and educational purposes. Please ensure compliance with the terms of service of the websites being scraped.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Open an issue with detailed error information

---

**Version**: 2.0 (Region Mode Only) 