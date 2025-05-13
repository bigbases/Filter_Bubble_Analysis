# LLM Persona-based Data Analyzation

This module analyzes news articles collected from search engines using multiple Large Language Models (LLMs) with different personas to evaluate political bias and stance across search results.

## Overview

The LLM Persona-based Data Analyzation module processes data collected by the Context-Aware Concurrent Data Collection module. It employs various large language models (LLMs) such as ChatGPT and Claude, each assuming different political personas to analyze news articles from multiple perspectives. This multi-dimensional analysis helps identify potential biases in search engine results based on user context.

## Architecture

```
LLM Persona-based Data Analyzation/
├── 1_llm-persona-based_data_analyzation.py  # Main data analysis script
├── 2_robust_parsing.py                      # Results parsing and processing script
├── chatgpt/                                 # ChatGPT request module
│   └── chatgpt_request.py                   # ChatGPT API request handler
├── claude/                                  # Claude request module
│   └── claude_request.py                    # Claude API request handler
└── prompt_fewshot_4dim_perspective/         # Prompt templates
    ├── prompt_content.txt                   # Content analysis template
    ├── prompt_role_opposed_left.txt         # Left-leaning opposed perspective template
    ├── prompt_role_opposed_right.txt        # Right-leaning opposed perspective template
    ├── prompt_role_supportive_left.txt      # Left-leaning supportive perspective template
    └── prompt_role_supportive_right.txt     # Right-leaning supportive perspective template
```

## Key Components

### Main Analysis Script (1_llm-persona-based_data_analyzation.py)

The main script loads data from the collection module and performs analysis using various LLM and persona combinations.

Key features:
- Loads all datasets within the specified date range
- Implements caching to prevent duplicate analysis
- Utilizes multiple LLM models (ChatGPT and Claude)
- Applies 4 different persona prompts
- Manages result storage and caching

### Results Parsing Script (2_robust_parsing.py)

This script parses and post-processes LLM responses into structured formats.

Key features:
- Regular expression-based JSON extraction and cleaning
- Data structuring and standardization
- Creates columns for each model and persona combination
- Robust error handling mechanisms
- Saves parsed results for further analysis

### LLM API Handlers

#### ChatGPT Handler (chatgpt/chatgpt_request.py)

This class manages communication with the ChatGPT API.

Key features:
- ChatGPT API connection and request handling
- System prompt and user message management
- Response validation and cleaning
- Automatic retry mechanism
- Error handling and logging

#### Claude Handler (claude/claude_request.py)

This class manages communication with the Claude API.

Key features:
- Claude API connection and request handling
- System prompt and user message management
- Response validation and cleaning
- Automatic retry mechanism
- Error handling and logging

### Prompt Templates

#### Content Prompt (prompt_content.txt)
Basic template for news article analysis, structuring the query, title, and content.

#### Persona Prompts
Four different perspective prompts:
- Left-leaning opposed perspective (prompt_role_opposed_left.txt)
- Right-leaning opposed perspective (prompt_role_opposed_right.txt)
- Left-leaning supportive perspective (prompt_role_supportive_left.txt)
- Right-leaning supportive perspective (prompt_role_supportive_right.txt)

Each prompt is designed to make the LLM assume the role of a professional annotator with specific political orientation and stance.

## Process Flow

1. **Data Loading**: Load datasets within the specified date range
2. **Persona Generation**: For each news article, generate 4 different persona perspectives
   - Left-leaning opposed (opp_left)
   - Right-leaning opposed (opp_right)
   - Left-leaning supportive (sup_left)
   - Right-leaning supportive (sup_right)
3. **LLM Requests**: Send each article to the specified LLMs (ChatGPT or Claude)
4. **Result Evaluation**: Each LLM evaluates the article in 4 dimensions
   - Political: Left, Center, Right
   - Stance: Against, Neutral, Support
5. **Result Storage**: Save evaluation results in JSON format
6. **Result Parsing**: Parse stored JSON responses into structured formats
7. **Data Merging**: Merge parsed results with the original dataset

## Analysis Dimensions

### Political
- Definition: The political leanings of the article
- Labels: [Left, Center, Right]
- Score: From -1 (extreme Left) to 1 (extreme Right), including decimal values

### Stance
- Definition: The article's position on the query topic
- Labels: [Against, Neutral, Support]
- Score: From -1 (strongly Against) to 1 (strongly Support), including decimal values

## Implementation Details

### Caching Mechanism
- URL-based caching to prevent duplicate analysis
- Model and persona-specific cache management
- In-memory cache for result persistence across sessions

### Result Parsing and Cleaning
- Regular expression-based JSON extraction
- Exception handling for robust operation
- Processing various LLM response formats

### Error Handling
- Retry mechanism with exponential backoff
- Error logging and monitoring
- Partial result saving and recovery

## Usage

1. Configure the LLM models to use in the script:
```python
claude_model_version_list = [
    'claude-3-5-sonnet-20241022'
]
chatgpt_model_version_list = [
    'gpt-4o'
]
```

2. Set the date range for processing:
```python
datetime_range = ['2024-09-21', '2024-09-30']
```

3. Run the main analysis script:
```bash
python 1_llm-persona-based_data_analyzation.py
```

4. After analysis, process and parse the results:
```bash
python 2_robust_parsing.py
```

5. Results will be saved to the specified output directory for further statistical analysis.

## Requirements

- Python 3.7+
- Required packages:
  - pandas
  - openai
  - anthropic
  - json
  - re
  - datetime

## API Keys

You'll need to insert your own API keys for:
- OpenAI API (for ChatGPT)
- Anthropic API (for Claude)

## Note

This module is designed to work with data collected by the Context-Aware Concurrent Data Collection module and provides input for the Statistical Significance Verification module.