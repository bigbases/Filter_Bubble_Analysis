# Context-Aware Concurrent Data Collection

A distributed system for context-aware web scraping using AWS Lambda functions to collect search results from multiple search engines (Bing News, Google News) with different contextual settings.

## Overview

This project implements a framework for collecting data from search engines with different contextual variables:
- Accept-Language settings
- User-Agent strings
- Geographic regions
- Search histories

The system uses a central manager that schedules and coordinates various data collection tasks, which are executed concurrently using AWS Lambda serverless functions.

## Architecture

- **Central Manager**: Orchestrates the data collection process by scheduling and managing concurrent tasks
- **Serverless Functions**: AWS Lambda functions distributed across regions to handle web requests
- **Service Modules**: Implementation for different search engines (Bing News, Google News)
- **Context Settings**: Configuration files for different contextual parameters (language, user agent, region)
- **Content Extractor**: Extracts full article content from collected URLs 

## Directory Structure

```
├── 1_central_manager.py       # Main orchestration script
├── 2_url_to_content.py        # Full content extraction from URLs
├── aws_functions.json         # AWS Lambda function definitions
├── topic.csv                  # Topics/queries for data collection
├── bing_news/                 # Bing News implementation
│   ├── create_region.py       # Region-based collection for Bing News
│   ├── accept_language.json   # Language settings
│   ├── user_agent.json        # User agent definitions
│   ├── headers.json           # HTTP headers configuration
│   └── cookies.json           # Cookie settings
├── google_news/               # Google News implementation
│   ├── create_region.py       # Region-based collection for Google News
│   ├── accept_language.json   # Language settings
│   ├── user_agent.json        # User agent definitions
│   ├── headers.json           # HTTP headers configuration
│   └── cookies.json           # Cookie settings
└── Serverless_Functions/      # AWS Lambda function code
    ├── aws_update.py          # Update Lambda functions
    ├── lambda_function.py     # Lambda function implementation
    └── deployment-package.zip # Lambda deployment package
```

## Functionality

1. **Concurrent Data Collection**: Uses ThreadPoolExecutor to parallelize data collection tasks across different contexts
2. **Distributed Scraping**: Leverages AWS Lambda functions across multiple regions to handle web requests
3. **Context Simulation**: Simulates different user contexts (language, region, user agent) for collecting diverse results
4. **Automatic Lambda Updates**: Includes functionality to automatically update Lambda functions when needed
5. **Full Content Extraction**: Extracts complete article content from the collected URLs

## Data Collection Workflow

### Stage 1: Search Results Collection
1. The central manager script (1_central_manager.py) schedules and initiates data collection tasks
2. Each service module (bing_news, google_news) implements data collection with different contextual parameters
3. AWS Lambda functions handle the actual web requests to avoid IP blocking and distribute load
4. Initial data (page, rank, source, title, snippet, URL) is stored in CSV format

### Stage 2: Full Content Extraction
1. The URL content extractor (2_url_to_content.py) processes the collected URLs from Stage 1
2. For each URL, it extracts the full article content using various techniques:
   - Newspaper3k library for general websites
   - Custom extraction for MSN.com articles
   - Fallback to Scrappey API for challenging websites
3. Content extraction is processed in parallel with configurable concurrency
4. Extracted content is cached to avoid redundant processing
5. Results are saved with the original data plus the full article content

## Data Collection Parameters

- **Topics**: Collected from `topic.csv`, current topics include "Abortion" and "Immigration"
- **Regions**: Multiple AWS regions: us-west-1, us-east-2, ap-northeast-2, ap-northeast-1, eu-west-2, eu-west-3
- **Accept-Language**: Various language settings defined in `accept_language.json`
- **User-Agent**: Different browser user agents defined in `user_agent.json`

## Requirements

- Python 3.x
- AWS credentials with Lambda access permissions
- Required Python packages:
  - boto3
  - requests
  - pandas
  - beautifulsoup4
  - concurrent.futures
  - newspaper3k
  - pickle

## Usage

1. Configure AWS credentials
2. Customize topics in `topic.csv`
3. Run the central manager to collect initial data:
```
python 1_central_manager.py
```
4. Extract full content from collected URLs:
```
python 2_url_to_content.py
```

## Lambda Function Management

- To update Lambda functions: `python Serverless_Functions/aws_update.py`
- Lambda functions are automatically updated if they encounter errors during scraping

## Data Output

### Initial Data (Stage 1)
Collected data is stored in CSV format with the following structure:
- page: Page number of search results
- rank: Position in search results
- source: Source of the news item
- title: Title of the search result
- content: Content snippet of the search result
- url: URL of the search result

### Full Content Data (Stage 2)
The final dataset includes all fields from Stage 1 plus:
- Article_Content: Full article text extracted from the URL