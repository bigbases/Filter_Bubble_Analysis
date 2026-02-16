# Statistical Significance Verification

This module performs comprehensive statistical analysis to verify the significance of search engine bias patterns across different user contexts, search engines, and topics using rigorous statistical methods.

## Overview

The Statistical Significance Verification module analyzes data processed by the LLM Persona-based Data Analysis module to determine whether observed differences in search results across various user contexts (geographic regions, language preferences, browser environments, and search histories) are statistically significant. It employs advanced statistical methods including normality testing, homogeneity of variance testing, parametric and non-parametric tests, multiple comparison corrections, and effect size calculations.

## Architecture

```
Statistical Significance Verification/
├── 1_statistical_significance_verfication.py  # Main statistical testing script
├── 2_statistical_results_vis.py               # Visualization of statistical results
├── README.md                                  # This documentation
└── 4/                                         # Output directory (auto-created)
    ├── aggregated_results/                    # Unique URL count data
    └── tests_<date>.csv                       # Statistical test results
```

## Key Components

### Statistical Testing Script (1_statistical_significance_verfication.py)

The main statistical analysis script performs comprehensive hypothesis testing on collected data.

**Core Features:**
- **Unique URL Count Calculation**: Determines sample sizes for each user context group
- **Assumption Testing**: 
  - Shapiro-Wilk test for normality assessment
  - Levene's test for homogeneity of variance
- **Statistical Tests**:
  - ANOVA (parametric) when assumptions are met
  - Kruskal-Wallis (non-parametric) when assumptions are violated
- **Post-hoc Analysis**: Tukey's HSD for pairwise comparisons after significant ANOVA
- **Effect Size Calculations**:
  - η² (eta-squared) and ω² (omega-squared) for ANOVA
  - η² (eta-squared) and ε² (epsilon-squared) for Kruskal-Wallis
- **Multiple Comparison Corrections**:
  - Bonferroni correction (family-wise error rate control)
  - Benjamini-Hochberg correction (false discovery rate control)
- **Robust Error Handling**: Comprehensive NaN value management and default value assignment

**Statistical Workflow:**
1. Load and process data from parsing results
2. Calculate unique URL counts by user context group
3. Extract bias scores from LLM analysis results
4. Test statistical assumptions (normality and homogeneity)
5. Apply appropriate statistical test based on assumption results
6. Calculate effect sizes and interpret magnitude
7. Apply multiple comparison corrections
8. Generate comprehensive results with metadata

### Visualization Script (2_statistical_results_vis.py)

Creates publication-quality visualizations of statistical analysis results.

**Visualization Features:**
- **Grid-based Layout**: Organized by search engine (rows) and query (columns)
- **P-value Representation**: 
  - Y-axis positioning based on significance levels
  - Reference lines at p=0.05 and p=0.01
- **Effect Size Encoding**:
  - Color intensity representing effect magnitude
  - Transparency (alpha) mapping for effect size interpretation
- **Context Information**: Unique URL counts displayed for each user context
- **Model Differentiation**: Distinct markers for different LLM models
- **Publication Quality**: 600 DPI output suitable for academic publications

**Output Components:**
- Main analysis plots showing significance patterns
- Effect size alpha legend for transparency interpretation
- Model marker legend for multi-model comparisons
- High-resolution PNG files optimized for publication

## Statistical Methodology

### Assumption Testing

Before applying parametric tests, the module performs rigorous assumption checking:

1. **Normality Testing**: Shapiro-Wilk test applied to each group
   - Null hypothesis: Data follows normal distribution
   - Significance level: α = 0.05

2. **Homogeneity of Variance**: Levene's test for equal variances
   - Null hypothesis: Variances are equal across groups
   - Significance level: α = 0.05

### Test Selection Logic

```
IF (normality_passed AND homogeneity_passed):
    Apply ANOVA F-test
    IF significant:
        Perform Tukey's HSD post-hoc test
ELSE:
    Apply Kruskal-Wallis H-test
    (Non-parametric alternative)
```

### Effect Size Interpretation

**ANOVA Effect Sizes:**
- η² (Eta-squared): Proportion of variance explained
- ω² (Omega-squared): Unbiased estimate of effect size

**Kruskal-Wallis Effect Sizes:**
- η² (Eta-squared): H/(n-1)
- ε² (Epsilon-squared): Adjusted eta-squared

**Interpretation Guidelines:**
- Negligible: < 0.01
- Small: 0.01 ≤ effect < 0.06  
- Medium: 0.06 ≤ effect < 0.14
- Large: ≥ 0.14

### Multiple Comparison Corrections

To address the multiple testing problem when conducting numerous statistical tests:

1. **Bonferroni Correction**: 
   - Conservative family-wise error rate control
   - Adjusted α = 0.05 / number_of_tests

2. **Benjamini-Hochberg Correction**:
   - Controls false discovery rate (FDR)
   - Less conservative than Bonferroni
   - Better balance between Type I and Type II errors

## Configuration

### Data Input Requirements

The module expects processed data from the LLM Persona-based Data Analysis module with the following structure:

```
parsing_folder/results_<date>/
├── YYYY-MM-DD/                    # Date folders
│   ├── <search_engine>/           # Google News, Bing News
│   │   └── <user_context>/        # Region, language, etc.
│   │       └── <query>_<details>.csv
```

### Required CSV Columns

Each input CSV file must contain:
- `url`: Unique article URLs for sample size calculation
- `<model>_<persona>_Political_Score`: Bias scores from LLM analysis
- `<model>_<persona>_Political_Label`: Political labels from LLM analysis

### Configuration Parameters

```python
# Directory settings
setting_date = '0921-30'  # Result folder identifier
datasets_file_path = f'../parsing_folder/results_{setting_date}'

# Statistical parameters
significance_level = 0.05  # Alpha level for hypothesis testing
sample_limit = 30  # Maximum articles per CSV file
```

## Usage Instructions

### Prerequisites

**Required Python packages:**
```bash
pip install pandas numpy scipy statsmodels matplotlib
```

**Required input data:**
- Processed results from LLM Persona-based Data Analysis module
- Properly structured directory hierarchy
- CSV files with required columns

### Running Statistical Analysis

1. **Configure data path:**
   ```python
   setting_date = 'your_date_identifier'
   ```

2. **Execute main analysis:**
   ```bash
   python 1_statistical_significance_verfication.py
   ```

3. **Generate visualizations:**
   ```bash
   python 2_statistical_results_vis.py
   ```

### Output Files

**Statistical Results:**
- `4/aggregated_results/aggregated_results.csv`: Unique URL counts
- `4/tests_<date>.csv`: Complete statistical test results

**Visualizations:**
- `5_1/main_analysis_plots.png`: Primary results visualization
- `5_1/effect_size_alpha_legend.png`: Effect size interpretation guide
- `5_1/model_legend.png`: Model marker reference

### Results Interpretation

**Statistical Significance:**
- `p_value < 0.05`: Statistically significant difference
- `bonferroni_significant`: Significance under conservative correction
- `bh_significant`: Significance under FDR correction

**Effect Size Assessment:**
- `effect_size`: Primary effect size measure
- `effect_size_secondary`: Alternative effect size measure
- `effect_interpretation`: Qualitative magnitude assessment

## Research Applications

This module is designed for academic research in:

- **Search Engine Bias Detection**: Quantifying bias patterns across platforms
- **Algorithmic Fairness**: Measuring differential treatment across user contexts
- **Information Access Equity**: Assessing content diversity across demographic groups
- **Computational Social Science**: Understanding algorithmic mediation of information

## Statistical Robustness

### Error Handling Strategy

The module implements comprehensive error handling:

1. **Missing Data Management**: NaN values replaced with conservative estimates
2. **Sample Size Validation**: Minimum group size requirements enforced
3. **Assumption Violation Handling**: Automatic fallback to non-parametric tests
4. **Correction Failure Recovery**: Manual correction application as backup

### Validation Measures

- **Assumption Testing**: Formal statistical tests before analysis
- **Effect Size Reporting**: Multiple effect size measures for robustness
- **Multiple Correction Methods**: Both conservative and FDR approaches
- **Comprehensive Logging**: Detailed error reporting and debugging information

## Performance Considerations

- **Memory Efficiency**: Processes data in chunks to manage memory usage
- **Computational Complexity**: O(n log n) for most statistical tests
- **Parallel Processing**: Designed for concurrent execution across date ranges
- **Scalability**: Handles datasets with thousands of articles and multiple contexts

## Troubleshooting

### Common Issues

1. **Missing Input Files**: Verify LLM analysis module has completed processing
2. **Column Name Mismatches**: Check that CSV headers match expected format
3. **Insufficient Sample Sizes**: Ensure adequate data collection for statistical power
4. **Memory Limitations**: Process smaller date ranges if encountering memory issues

### Debug Mode

Enable detailed logging by modifying the print statements in the main script.

## License

This project is for research and educational purposes. Ensure compliance with:
- Institutional Review Board (IRB) requirements for human subjects research
- Data protection regulations (GDPR, CCPA, etc.)
- Academic integrity standards for statistical reporting

## Publication

**Paper Title**: FAIR-SE: Framework for Analyzing Information Disparities in Search Engines with Diverse LLM-Generated Personas

**Authors**: Jaebeom You, Seung-Kyu Hong, Ling Liu, Kisung Lee, Hyuk-Yoon Kwon

**Conference**: Proceedings of the 34th ACM International Conference on Information and Knowledge Management

**Year**: 2025

**DOI**: ---

**Published**: November 10--14, 2025

**Link**: ---

---

**Version**: 2.0  
**Last Updated**: 2024  
**Status**: Research Tool for Academic Publication
