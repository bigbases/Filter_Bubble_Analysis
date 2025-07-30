# LLM Persona-based Data Analysis

This module analyzes news articles collected from search engines using multiple Large Language Models (LLMs) with different personas to evaluate political bias and stance across search results.

## Overview

The LLM Persona-based Data Analysis module processes data collected by the Context-Aware Concurrent Data Collection module. It employs various large language models (LLMs) such as ChatGPT and Claude, each assuming different political personas to analyze news articles from multiple perspectives. This multi-dimensional analysis helps identify potential biases in search engine results based on user context.

## Architecture

```
LLM Persona-based Data Analysis/
├── 1_llm-persona-based_data_analyzation.py  # Main data analysis script
├── 2_robust_parsing.py                      # Results parsing and processing script
├── chatgpt/                                 # ChatGPT request module
│   └── chatgpt_request.py                   # ChatGPT API request handler
├── claude/                                  # Claude request module
│   └── claude_request.py                    # Claude API request handler
├── prompt/                                  # Prompt templates
│   ├── prompt_content.txt                   # Content analysis template
│   ├── prompt_role_opposed_left.txt         # Left-leaning opposed perspective template
│   ├── prompt_role_opposed_right.txt        # Right-leaning opposed perspective template
│   ├── prompt_role_supportive_left.txt      # Left-leaning supportive perspective template
│   └── prompt_role_supportive_right.txt     # Right-leaning supportive perspective template
└── README.md                                # This documentation
```

## Key Components

### Main Analysis Script (1_llm-persona-based_data_analyzation.py)

The main script loads data from the collection module and performs analysis using various LLM and persona combinations.

**Key features:**
- Loads all datasets within the specified date range
- Implements caching to prevent duplicate analysis
- Utilizes multiple LLM models (ChatGPT and Claude)
- Applies 4 different persona prompts
- Manages result storage and caching
- Rate limiting to respect API constraints
- Robust error handling and retry mechanisms

**Usage:**
```python
# Configure model versions and date range
claude_model_version_list = ['claude-3-5-sonnet-20241022']
chatgpt_model_version_list = ['gpt-4o']
datetime_range = ['2024-09-24', '2024-09-30']

# Execute analysis
get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list, endswith_date)
```

### Results Parsing Script (2_robust_parsing.py)

This script parses and post-processes LLM responses into structured formats.

**Key features:**
- Regular expression-based JSON extraction and cleaning
- Data structuring and standardization
- Creates columns for each model and persona combination
- Robust error handling mechanisms
- Saves parsed results for further analysis

**Functions:**
- `parse_response()`: Parse JSON responses into structured format
- `clean_json_string()`: Clean and prepare JSON strings
- `robust_json_extract()`: Extract JSON using multiple fallback strategies

### API Clients

#### ChatGPT Client (chatgpt/chatgpt_request.py)
- Handles OpenAI ChatGPT API interactions
- Response validation and retry logic
- JSON extraction from responses

#### Claude Client (claude/claude_request.py)
- Handles Anthropic Claude API interactions
- System message management
- Response validation and retry logic

### Persona Framework

The system uses four distinct political personas to analyze each article:

1. **Opposed Left (opp_left)**: Left-leaning perspective opposing the article's stance
2. **Opposed Right (opp_right)**: Right-leaning perspective opposing the article's stance  
3. **Supportive Left (sup_left)**: Left-leaning perspective supporting the article's stance
4. **Supportive Right (sup_right)**: Right-leaning perspective supporting the article's stance

## Configuration

### API Keys

Set your API keys as environment variables or update the client files:

```python
# For ChatGPT
self.OPENAI_API_KEY = '<your-openai-api-key>'

# For Claude  
self.API_KEY = '<your-anthropic-api-key>'
```

### Model Versions

Configure the models you want to use:

```python
claude_model_version_list = [
    'claude-3-5-sonnet-20241022',
    # Add other Claude models
]

chatgpt_model_version_list = [
    'gpt-4o',
    'gpt-4-turbo',
    # Add other ChatGPT models
]
```

### Date Range

Specify the date range for analysis:

```python
datetime_range = ['2024-09-24', '2024-09-30']  # [start_date, end_date]
```

## Output Format

### Analysis Results

Each article is analyzed and produces structured JSON responses:

```json
{
  "Political": {
    "label": "Left|Center|Right",
    "score": -1.0 to 1.0
  },
  "Stance": {
    "label": "Support|Oppose|Neutral", 
    "score": -1.0 to 1.0
  },
  "Reasoning": "Detailed explanation of the analysis"
}
```

### CSV Structure

The output CSV contains columns for each model-persona combination:

```csv
url,title,content,gpt-4o_opp_left,gpt-4o_opp_right,claude-3-5-sonnet_sup_left,...
```

### Parsed Results

After parsing, additional columns are created:

```csv
...,gpt-4o_opp_left_Political_Label,gpt-4o_opp_left_Political_Score,gpt-4o_opp_left_Stance_Label,...
```

## Usage Instructions

### Prerequisites

1. Python 3.8+
2. Required packages: `pandas`, `openai`, `anthropic`
3. Valid API keys for OpenAI and/or Anthropic
4. Data from Context-Aware Concurrent Data Collection module

### Installation

```bash
pip install pandas openai anthropic
```

### Running Analysis

1. **Set up API keys** in the respective client files
2. **Configure models and date range** in the main script
3. **Run the main analysis:**
   ```bash
   python 1_llm-persona-based_data_analyzation.py
   ```
4. **Parse the results:**
   ```bash
   python 2_robust_parsing.py
   ```

### Batch Processing

For large datasets, the system includes:
- Automatic caching to avoid reprocessing
- Rate limiting to respect API constraints
- Progress tracking and logging
- Resume capability for interrupted runs

## Performance Considerations

- **API Rate Limits**: Built-in delays between requests
- **Caching**: Avoids duplicate analysis of same articles
- **Batch Processing**: Processes files sequentially to manage memory
- **Error Handling**: Continues processing even if individual requests fail

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure valid API keys are set
2. **Rate Limiting**: Increase delays between requests if needed
3. **JSON Parsing Errors**: Check LLM response formats
4. **File Not Found**: Verify data directory structure

### Debug Mode

Enable detailed logging by modifying the print statements in the scripts.

### Memory Management

For large datasets:
- Process files in smaller batches
- Clear cache periodically
- Monitor system memory usage

## Research Applications

This module is designed for academic research on:
- Search engine bias detection
- Political content analysis
- Multi-perspective information evaluation
- LLM-based content classification

## License

This project is for research and educational purposes. Ensure compliance with:
- OpenAI API Terms of Service
- Anthropic API Terms of Service
- Relevant data protection regulations

## Citation

When using this module in research, please cite:
```
[Research Team]. (2024). LLM Persona-based Data Analysis Module. 
Context-Aware Search Engine Bias Detection Framework.
```

---

**Version**: 2.0  
**Last Updated**: 2024  
**Status**: Research Tool