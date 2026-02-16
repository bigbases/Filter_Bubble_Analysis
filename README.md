# Search Engine Bias Analysis Framework

A comprehensive research framework for detecting and analyzing information disparities in search engine results using diverse LLM-generated personas across multiple user contexts.

## Publication

**Paper Title**: Geo-Personalization Bias in News Search: Analyzing Filter Bubbles in Search Engine Results with Multi-Perspective LLM

**Authors**: Jaebeom You, Seung-Kyu Hong, Ling Liu, Kisung Lee, Hyuk-Yoon Kwon

**Conference**: Proceedings of the 19th ACM International Conference on Web Search and Data Mining

**Year**: 2026

**DOI**: ---

**Published**: February 22--26, 2026

**Link**: ---

## Overview

This is a three-stage research framework designed to systematically detect, analyze, and verify information disparities in search engine results. The framework combines context-aware web scraping, LLM-based multi-perspective analysis, and rigorous statistical testing to quantify bias patterns across different user contexts.

## Framework Architecture

```
EMNLP/
├── Context-Aware Concurrent Data Collection/  # Stage 1: Data Collection
├── LLM Persona-based Data Analyzation/        # Stage 2: LLM Analysis
├── Statistical Significance Verification/     # Stage 3: Statistical Testing
├── Prompt/                                    # Shared Prompt Templates
├── datasets/                                  # Collected Data Storage
└── README.md                                  # This Documentation
```

## Pipeline Stages

### Stage 1: Context-Aware Concurrent Data Collection

**Purpose**: Collect news articles from multiple search engines across diverse geographical contexts.

**Key Features**:
- Multi-source scraping (Google News, Bing News)
- 6 AWS regions for geographical diversity (US West, US East, Tokyo, Seoul, Paris, London)
- Concurrent processing via AWS Lambda for efficiency
- Real-time data saving and deduplication

**Main Components**:
- `start.py` - Main entry point for data collection
- `detail_content_scraper.py` - Core scraping engine
- `data_processor.py` - Data cleaning and processing
- AWS Lambda integration for distributed scraping

**Output**: 
- CSV files organized by date, search engine, region, and topic
- Location: `datasets/YYYY-MM-DD/[google_news|bing_news]/region/`

**Usage**:
```bash
cd "Context-Aware Concurrent Data Collection"
python start.py all  # Run collection across all regions
```

📖 [Detailed Documentation](./Context-Aware%20Concurrent%20Data%20Collection/README.md)

---

### Stage 2: LLM Persona-based Data Analyzation

**Purpose**: Analyze collected articles using multiple LLMs with different political personas to evaluate bias from various perspectives.

**Key Features**:
- Multiple LLM support (ChatGPT, Claude)
- 4 distinct political personas (opposed left/right, supportive left/right)
- Automated political leaning and stance detection
- Robust JSON parsing and error handling

**Main Components**:
- `1_llm-persona-based_data_analyzation.py` - Main analysis script
- `2_robust_parsing.py` - Results parsing and structuring
- `chatgpt/chatgpt_request.py` - OpenAI API client
- `claude/claude_request.py` - Anthropic API client

**Analysis Dimensions**:
- **Political Leaning**: Left (-1.0) ← Center (0) → Right (+1.0)
- **Stance**: Oppose (-1.0) ← Neutral (0) → Support (+1.0)

**Output**:
- Parsed CSV files with political scores and labels
- One column per model-persona combination
- JSON responses with reasoning

**Usage**:
```bash
cd "LLM Persona-based Data Analyzation"
python 1_llm-persona-based_data_analyzation.py  # Run LLM analysis
python 2_robust_parsing.py                       # Parse results
```

📖 [Detailed Documentation](./LLM%20Persona-based%20Data%20Analyzation/README.md)

---

### Stage 3: Statistical Significance Verification

**Purpose**: Verify statistical significance of observed bias patterns using rigorous statistical methods.

**Key Features**:
- Comprehensive assumption testing (normality, homogeneity)
- Parametric (ANOVA) and non-parametric (Kruskal-Wallis) tests
- Multiple comparison corrections (Bonferroni, Benjamini-Hochberg)
- Effect size calculations (η², ω², ε²)
- Publication-quality visualizations

**Main Components**:
- `1_statistical_significance_verfication.py` - Statistical testing
- `2_statistical_results_vis.py` - Results visualization

**Statistical Methods**:
1. Shapiro-Wilk test for normality
2. Levene's test for homogeneity of variance
3. ANOVA F-test or Kruskal-Wallis H-test
4. Tukey's HSD post-hoc analysis
5. Multiple comparison corrections

**Output**:
- Statistical test results CSV with p-values and effect sizes
- High-resolution visualization plots (600 DPI)
- Effect size interpretation guides

**Usage**:
```bash
cd "Statistical Significance Verification"
python 1_statistical_significance_verfication.py  # Run statistical tests
python 2_statistical_results_vis.py                # Generate visualizations
```

📖 [Detailed Documentation](./Statistical%20Significance%20Verification/README.md)

---

### Shared Resources: Prompt Templates

**Purpose**: Standardized prompt templates for LLM-based article analysis.

**Location**: `Prompt/`

**Templates**:
- `prompt_role_opposed_left.txt` - Left-leaning opposed perspective
- `prompt_role_opposed_right.txt` - Right-leaning opposed perspective
- `prompt_role_supportive_left.txt` - Left-leaning supportive perspective
- `prompt_role_supportive_right.txt` - Right-leaning supportive perspective

**Format**: Each prompt produces structured JSON output with political leaning, stance, and reasoning.

📖 [Detailed Documentation](./Prompt/README.md)

---

## Quick Start Guide

### Prerequisites

```bash
# Python 3.8+
pip install pandas numpy scipy statsmodels matplotlib openai anthropic

# AWS credentials for data collection
aws configure
```

### Complete Pipeline Execution

```bash
# Step 1: Collect data
cd "Context-Aware Concurrent Data Collection"
python start.py all

# Step 2: Analyze with LLMs
cd "../LLM Persona-based Data Analyzation"
python 1_llm-persona-based_data_analyzation.py
python 2_robust_parsing.py

# Step 3: Statistical verification
cd "../Statistical Significance Verification"
python 1_statistical_significance_verfication.py
python 2_statistical_results_vis.py
```

## Configuration

### API Keys Setup

**OpenAI (ChatGPT)**:
```python
# In chatgpt/chatgpt_request.py
self.OPENAI_API_KEY = '<your-openai-api-key>'
```

**Anthropic (Claude)**:
```python
# In claude/claude_request.py
self.API_KEY = '<your-anthropic-api-key>'
```

### AWS Lambda Setup

Configure Lambda functions in `Context-Aware Concurrent Data Collection/aws/aws_functions.json` with your Lambda ARNs for each region.

### Date Range Configuration

Update date ranges in analysis scripts:
```python
datetime_range = ['2024-09-24', '2024-09-30']  # [start, end]
```

## Data Flow

```
1. Data Collection
   └─> datasets/YYYY-MM-DD/[google_news|bing_news]/region/*.csv

2. LLM Analysis
   └─> parsing_folder/results_*/YYYY-MM-DD/[search_engine]/[context]/*.csv

3. Statistical Testing
   └─> 4/tests_*.csv (results)
   └─> 5_1/*.png (visualizations)
```

## Research Applications

This framework is designed for academic research in:

- **Search Engine Bias Detection**: Quantifying bias patterns across platforms
- **Algorithmic Fairness**: Measuring differential treatment across user contexts
- **Information Access Equity**: Assessing content diversity across demographics
- **Computational Social Science**: Understanding algorithmic information mediation
- **Media Studies**: Analyzing political leaning in news coverage

## Project Structure Summary

| Module | Purpose | Key Output |
|--------|---------|------------|
| Context-Aware Concurrent Data Collection | Collect news articles from multiple regions | CSV files with articles |
| LLM Persona-based Data Analyzation | Analyze political bias using LLM personas | CSV files with bias scores |
| Statistical Significance Verification | Verify statistical significance of patterns | Statistical results + plots |
| Prompt | Provide standardized analysis templates | Reusable prompt templates |

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: 8GB+ RAM recommended
- **Storage**: Depends on data collection scope
- **Network**: Stable connection for API calls
- **AWS**: Account with Lambda deployment capabilities

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: Adjust delays in LLM request modules
2. **AWS Lambda Timeout**: Increase timeout settings in Lambda configuration
3. **Memory Issues**: Process data in smaller batches
4. **Missing Dependencies**: Run `pip install -r requirements.txt` in each module