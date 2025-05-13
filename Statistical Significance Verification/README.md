# Statistical Significance Verification

This module performs robust statistical testing to verify the significance of search engine bias patterns across different user contexts, search engines, and topics.

## Overview

The Statistical Significance Verification module analyzes the data processed by the LLM Persona-based Data Analyzation module to determine whether the observed differences in search results across various user contexts (language preferences, geographic regions, browser environments, and search histories) are statistically significant. It employs rigorous statistical methods, including normality testing, homogeneity of variance testing, parametric and non-parametric tests, multiple comparison corrections, and effect size calculations.

## Architecture

```
Statistical Significance Verification/
├── 1_statistical_significance_verfication.py  # Main statistical testing script
└── 2_statistical_results_vis.py               # Visualization of statistical results
```

## Key Components

### Statistical Testing (1_statistical_significance_verfication.py)

This script performs comprehensive statistical analysis on the collected and processed data.

Key features:
- Unique URL count calculation for each user context group
- Normality testing using Shapiro-Wilk test
- Homogeneity of variance testing using Levene's test
- Parametric testing (ANOVA) when normality and homogeneity assumptions are met
- Non-parametric testing (Kruskal-Wallis) when assumptions are not met
- Post-hoc testing with Tukey's HSD for significant ANOVA results
- Effect size calculation (η² and ω² for ANOVA, η² and ε² for Kruskal-Wallis)
- Multiple comparison corrections:
  - Bonferroni correction (more conservative)
  - Benjamini-Hochberg correction (controls false discovery rate)
- Robust error handling and NaN value management
- Comprehensive result storage with metadata

### Visualization (2_statistical_results_vis.py)

This script creates visualizations of the statistical analysis results.

Key features:
- Grid-based plots organized by search engine and query
- Visualization of p-values with significance threshold indicators
- Effect size representation through color and opacity
- Unique URL count display for each context
- Time-series view across multiple dates
- Model-specific marker differentiation
- Legend creation for models and effect sizes
- High-quality image output for publication

## Process Flow

1. **Data Collection**: The module begins by collecting all processed data from the LLM Persona-based Data Analyzation module.

2. **URL Count Calculation**: For each combination of date, search engine, user context, and query, the unique URL count is calculated.

3. **Score Extraction**: For each model dimension (Political, Stance, Subjectivity, Bias), scores are extracted and grouped by user context.

4. **Statistical Testing**:
   - Data normalization and NaN removal
   - Normality testing with Shapiro-Wilk
   - Homogeneity testing with Levene's test
   - ANOVA or Kruskal-Wallis testing based on data characteristics
   - Effect size calculation
   - Multiple comparison corrections

5. **Result Compilation**: All test results are compiled into a comprehensive dataframe with metadata.

6. **Visualization**: Results are visualized in a grid layout, highlighting significant findings.

## Statistical Methods

### Normality Testing
- **Method**: Shapiro-Wilk Test
- **Purpose**: Determine if data follows a normal distribution
- **Criterion**: p-value ≥ 0.05 indicates normal distribution

### Homogeneity Testing
- **Method**: Levene's Test
- **Purpose**: Determine if variances are equal across groups
- **Criterion**: p-value ≥ 0.05 indicates homogeneous variances

### Parametric Testing
- **Method**: One-way ANOVA
- **Purpose**: Compare means across multiple groups
- **Requirements**: Data must be normally distributed with homogeneous variances
- **Post-hoc**: Tukey's HSD for pairwise comparisons when ANOVA is significant

### Non-parametric Testing
- **Method**: Kruskal-Wallis Test
- **Purpose**: Compare distributions across multiple groups
- **Used when**: Data violates normality or homogeneity assumptions

### Effect Size Calculation
- **For ANOVA**:
  - Eta Squared (η²): Proportion of total variance attributed to an effect
  - Omega Squared (ω²): Less biased estimate of variance explained
- **For Kruskal-Wallis**:
  - Eta Squared (η²): H/(n-1)
  - Epsilon Squared (ε²): H/(n-1)/(n+1)
- **Interpretation**:
  - < 0.01: Negligible effect
  - < 0.06: Small effect
  - < 0.14: Medium effect
  - ≥ 0.14: Large effect

### Multiple Comparison Corrections
- **Bonferroni Correction**:
  - Adjusted p-value = p-value × number of tests
  - Controls family-wise error rate
  - Very conservative
- **Benjamini-Hochberg Correction**:
  - Controls false discovery rate (FDR)
  - Less conservative than Bonferroni
  - More statistical power

## Visualization Elements

The visualization script creates grid plots with the following elements:
- **X-axis**: User contexts grouped by date
- **Y-axis**: p-values (0 to 1)
- **Horizontal line**: Significance threshold (p = 0.05)
- **Markers**: Different shapes for different LLM dimensions
- **Opacity**: Represents effect size magnitude
- **Border**: Significant results (p < 0.05) are highlighted with borders
- **Text annotations**: Unique URL counts for each context

## Usage

1. Ensure the LLM Persona-based Data Analyzation module has processed the data.

2. Configure the date range in the script:
```python
setting_date = '0921-30'  # Modify as needed
```

3. Run the statistical testing script:
```bash
python 1_statistical_significance_verfication.py
```

4. Run the visualization script:
```bash
python 2_statistical_results_vis.py
```

5. Results will be saved to:
   - Statistical test results: `4/tests_{setting_date}.csv`
   - Visualizations: `5_1/p_value_trends_{search_engine}.png`

## Requirements

- Python 3.7+
- Required packages:
  - pandas
  - numpy
  - scipy
  - statsmodels
  - matplotlib
  - math
  - re
  - datetime

## Output Files

- **Test Results**: CSV file containing all statistical test results
- **Visualization**: PNG files showing p-value trends across different search engines, queries, and user contexts

## Note

This module is designed to work with data processed by the LLM Persona-based Data Analyzation module and provides rigorous statistical evidence for the presence or absence of search engine bias across different user contexts.
