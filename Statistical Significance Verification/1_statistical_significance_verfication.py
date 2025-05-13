import pandas as pd
import os
from scipy.stats import kruskal, f_oneway, shapiro, levene
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import numpy as np
from datetime import datetime
import re
import traceback
import math

# Set the directory and fetch the dataset files
current_dir = os.path.dirname(os.path.abspath(__file__))
# cache_2dim_political_stance_personas
setting_date = '0921-30'
datasets_file_path = os.path.join(current_dir, f'../parsing_folder/results_{setting_date}')
datetime_folders = [folder for folder in os.listdir(datasets_file_path) if os.path.isdir(os.path.join(datasets_file_path, folder))]

# Dictionary to store all statistical test results
pf_model_comparisons = {}

# 1. 먼저 각 그룹별 고유 URL 수를 계산합니다
def calculate_unique_url_counts():
    # Create a list to store all dataframes
    all_dfs = []

    # Process datasets
    for datetime_folder in datetime_folders:
        folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
        pir_folders = [folder for folder in os.listdir(os.path.join(datasets_file_path, datetime_folder))]
        pir_path = os.path.join(datasets_file_path, datetime_folder)

        for pir_folder in pir_folders:
            pf_folders = [folder for folder in os.listdir(os.path.join(pir_path, pir_folder))]
            pf_path = os.path.join(datasets_file_path, datetime_folder, pir_folder)

            for pf_folder in pf_folders:
                csv_files = [file for file in os.listdir(os.path.join(pf_path, pf_folder)) if file.endswith('.csv')]
                csv_files = sorted(csv_files)
                final_path = os.path.join(pf_path, pf_folder)

                for file in csv_files:
                    try:
                        df = pd.read_csv(os.path.join(final_path, file), encoding='utf-8')[:30]
                        
                        # Add metadata columns
                        df['query'] = file.split('_')[0].lower()
                        df['pf_folder_Details'] = '_'.join(file.replace('.csv', '').split('_')[1:])
                        df['datetime_folder'] = datetime_folder
                        df['pir_folder'] = pir_folder
                        df['pf_folder'] = pf_folder
                        
                        all_dfs.append(df)
                    except Exception as e:
                        print(f"Error reading file {file}: {e}")
                        continue

    # Combine all dataframes
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Group by datetime_folder, pir_folder, pf_folder, and query, count unique URLs
        result_df = (combined_df.groupby(['datetime_folder', 'pir_folder', 'pf_folder', 'query'])
                    .agg({'url': 'nunique'})  # Assumes 'url' is the column name for URLs
                    .reset_index()
                    .rename(columns={'url': 'Unique_URL_Count'}))

        print("Unique URL counts calculated successfully!")
        return result_df
    else:
        print("No data found to calculate unique URL counts.")
        return pd.DataFrame(columns=['datetime_folder', 'pir_folder', 'pf_folder', 'query', 'Unique_URL_Count'])

# 고유 URL 수 계산 및 저장
unique_url_counts_df = calculate_unique_url_counts()

# 필요한 경우 저장
if not os.path.exists(os.path.join(current_dir, f'4/aggregated_results')):
    os.makedirs(os.path.join(current_dir, f'4/aggregated_results'))
unique_url_counts_df.to_csv(os.path.join(current_dir, f'4/aggregated_results/aggregated_results.csv'), index=False)


def calculate_kruskal_effect_size(stat, n_total, n_groups):
    """
    Kruskal-Wallis 테스트의 effect size (η² or ε²)를 계산합니다.
    
    Args:
        stat: Kruskal-Wallis H 통계량
        n_total: 전체 샘플 크기
        n_groups: 그룹 수
    
    Returns:
        eta_squared: Kruskal-Wallis의 이타 제곱 effect size
        epsilon_squared: Kruskal-Wallis의 엡실론 제곱 effect size
        해석 정보
    """
    try:
        # 이타 제곱(η²) 계산: H/(n-1)
        if n_total <= 1:
            return 0.0, 0.0, "negligible"
            
        eta_squared = stat / (n_total - 1)
        
        # 엡실론 제곱(ε²) 계산: H/(n-1)/(n+1)
        epsilon_squared = eta_squared * ((n_total - 1) / (n_total + 1))
        
        # 해석 정보
        interpretation = ""
        if eta_squared < 0.01:
            interpretation = "negligible"
        elif eta_squared < 0.06:
            interpretation = "small"
        elif eta_squared < 0.14:
            interpretation = "medium"
        else:
            interpretation = "large"
    except Exception as e:
        print(f"Error calculating Kruskal-Wallis effect size: {e}")
        return 0.0, 0.0, "negligible"
        
    return eta_squared, epsilon_squared, interpretation


def calculate_anova_effect_size(groups):
    """
    ANOVA의 effect size (η² and ω²)를 계산합니다.
    
    Args:
        groups: 데이터 그룹의 리스트
    
    Returns:
        eta_squared: ANOVA의 이타 제곱 effect size
        omega_squared: ANOVA의 오메가 제곱 effect size
        해석 정보
    """
    try:
        # 전체 데이터 병합
        all_data = np.concatenate(groups)
        n_total = len(all_data)
        
        # 그룹 간 자유도
        df_between = len(groups) - 1
        
        # 그룹 내 자유도
        df_within = n_total - len(groups)
        
        if df_within <= 0 or df_between <= 0:
            return 0.0, 0.0, "negligible"
        
        # 전체 평균
        grand_mean = np.mean(all_data)
        
        # 그룹 평균
        group_means = [np.mean(group) for group in groups]
        
        # 그룹 크기
        group_sizes = [len(group) for group in groups]
        
        # 그룹 간 제곱합 (SSB)
        ss_between = sum(size * (mean - grand_mean)**2 for size, mean in zip(group_sizes, group_means))
        
        # 전체 제곱합 (SST)
        ss_total = sum((x - grand_mean)**2 for x in all_data)
        
        # 그룹 내 제곱합 (SSW)
        ss_within = ss_total - ss_between
        
        # 이타 제곱(η²) 계산
        if ss_total == 0:
            eta_squared = 0.0
        else:
            eta_squared = ss_between / ss_total
        
        # 오메가 제곱(ω²) 계산
        ms_within = ss_within / df_within
        
        # 오메가 제곱 분모 검사
        denominator = ss_total + ms_within
        if denominator <= 0:  # 분모가 0이거나 음수인 경우
            omega_squared = 0
        else:
            omega_squared = (ss_between - (df_between * ms_within)) / denominator
        
        # 해석 정보
        interpretation = ""
        if eta_squared < 0.01:
            interpretation = "negligible"
        elif eta_squared < 0.06:
            interpretation = "small"
        elif eta_squared < 0.14:
            interpretation = "medium"
        else:
            interpretation = "large"
    except Exception as e:
        print(f"Error calculating ANOVA effect size: {e}")
        return 0.0, 0.0, "negligible"
        
    return eta_squared, omega_squared, interpretation


def apply_corrections(test_results):
    """
    검색엔진×쿼리 기반으로 그룹화하여 Benjamini-Hochberg와 본페로니 교정을 모두 적용합니다.
    
    Args:
        test_results: 테스트 결과를 포함하는 딕셔너리
        
    Returns:
        두 교정 방법이 적용된 업데이트된 테스트 결과
    """
    # 모든 키에 필요한 필드가 있는지 확인
    for key, info in list(test_results.items()):
        missing_keys = []
        for expected_key in ['p_value']:
            if expected_key not in info:
                missing_keys.append(expected_key)
        
        if missing_keys:
            print(f"Missing keys {missing_keys} in test result for {key}. Adding default values.")
            for missing_key in missing_keys:
                test_results[key][missing_key] = 1.0  # 기본값으로 1.0 설정 (가장 보수적인 p-value)
    
    # 검색엔진(pir_folder)과 쿼리로 그룹화
    grouped_tests = {}
    for key, info in test_results.items():
        # search_engine = key[1]  # pir_folder는 검색엔진을 나타냄
        # query = key[3]
        # group_key = (search_engine, query)
        search_engine = key[1]  # 검색엔진
        context = key[2]        # 사용자 컨텍스트
        model_name = key[4]     # 분석 관점
        
        group_key = (search_engine, context, model_name)
            
        if group_key not in grouped_tests:
            grouped_tests[group_key] = []
        
        # p_value가 NaN이면 1.0으로 대체 (가장 보수적인 p-value)
        p_value = info.get('p_value', 1.0)
        if np.isnan(p_value):
            p_value = 1.0
            test_results[key]['p_value'] = p_value
        
        grouped_tests[group_key].append((key, p_value))
    
    # 각 그룹별로 교정 적용
    for group_key, tests in grouped_tests.items():
        keys = [t[0] for t in tests]
        p_values = [t[1] for t in tests]
        
        # NaN 값 확인
        if any(np.isnan(p) for p in p_values):
            print(f"Warning: NaN p-values found in group {group_key}. Replacing with 1.0")
            p_values = [p if not np.isnan(p) else 1.0 for p in p_values]
        
        # 본페로니 교정
        n_tests = len(p_values)
        bonferroni_alpha = 0.05 / n_tests
        bonferroni_adjusted = [min(p * n_tests, 1.0) for p in p_values]
        
        try:
            # Benjamini-Hochberg 교정
            _, bh_adjusted_p_values, _, _ = multipletests(
                p_values,
                alpha=0.05,
                method='fdr_bh'
            )
        except Exception as e:
            print(f"Error applying BH correction for group {group_key}: {e}")
            bh_adjusted_p_values = [min(p * 2, 1.0) for p in p_values]  # 보수적인 대체값
        
        # 두 교정 방법의 결과를 원래 결과에 추가
        for i, key in enumerate(keys):
            test_results[key]['bonferroni_p_value'] = bonferroni_adjusted[i]
            test_results[key]['bh_adjusted_p_value'] = bh_adjusted_p_values[i]
            test_results[key]['bonferroni_significant'] = p_values[i] < bonferroni_alpha
            test_results[key]['bh_significant'] = bh_adjusted_p_values[i] < 0.05
            # 그룹 정보 추가
            test_results[key]['correction_group'] = f"{group_key[0]}_{group_key[1]}"
            test_results[key]['group_size'] = n_tests
    
    return test_results

def normalize_data_length(scores_by_pf):
    min_length = min(len(scores) for scores in scores_by_pf.values())
    return {pf: scores[:min_length] for pf, scores in scores_by_pf.items()}

def ensure_numeric(scores_list):
    """
    Convert scores to numeric and explicitly remove NaN values.
    Returns cleaned scores list only containing valid numeric values.
    
    Args:
        scores_list: List of score arrays
    Returns:
        List of cleaned numpy arrays with NaN values removed
    """
    cleaned_scores = []
    for scores in scores_list:
        # Convert to numpy array if not already
        scores_array = np.array(scores, dtype=float)
        
        # Remove NaN values
        valid_scores = scores_array[~np.isnan(scores_array)]
        
        # Only include if we have valid data after cleaning
        if len(valid_scores) > 0:
            cleaned_scores.append(valid_scores)
            # print(f"Original length: {len(scores_array)}, After NaN removal: {len(valid_scores)}")
        else:
            print(f"Warning: All values were NaN in one of the score arrays")
    
    return cleaned_scores

for datetime_folder in datetime_folders:
    folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
    pir_folders = [folder for folder in os.listdir(os.path.join(datasets_file_path, datetime_folder))]
    pir_path = os.path.join(datasets_file_path, datetime_folder)

    for pir_folder in pir_folders:
        pf_folders = [folder for folder in os.listdir(os.path.join(pir_path, pir_folder))]
        pf_path = os.path.join(datasets_file_path, datetime_folder, pir_folder)

        for pf_folder in pf_folders:
            csv_files = [file for file in os.listdir(os.path.join(pf_path, pf_folder)) if file.endswith('.csv')]
            csv_files = sorted(csv_files)
            final_path = os.path.join(pf_path, pf_folder)

            model_scores = {model_name: {} for model_name in ['Political_Score', 'Stance_Score']}

            for file in csv_files:
                try:
                    df = pd.read_csv(os.path.join(final_path, file), encoding='utf-8')[:30]
                except:
                    continue  # Handling file read errors

                file_name = file.replace('.csv', '')
                query = file_name.split('_')[0]
                # 쿼리문 소문자로 통일  
                query = query.lower()
                pf = tuple(file_name.split('_')[1:])

                for model_name in model_scores:
                    pattern = re.compile(f'{model_name}$', re.IGNORECASE)
                    cols_to_read = [col for col in df.columns if pattern.search(col)]
                    # print(f"Reading {model_name} for {datetime_folder}, {pir_folder}, {pf_folder}, {query}")
                    # print(f"cols_to_read: {cols_to_read}")
                    # print(df[cols_to_read].head())
                    df_model = df[cols_to_read].mean(axis=1).values
                    # print(f"df_model: {df_model}")
                    if query not in model_scores[model_name]:
                        model_scores[model_name][query] = {}
                    if pf not in model_scores[model_name][query]:
                        model_scores[model_name][query][pf] = []

                    model_scores[model_name][query][pf].extend(df_model)

            # Perform statistical tests depending on the folder and conditions
            for model_name, queries in model_scores.items():
                for query, scores_by_pf in queries.items():
                    scores_by_pf = normalize_data_length(scores_by_pf)
                    num_comparisons = len(scores_by_pf) * (len(scores_by_pf) - 1) / 2  # Calculate the number of comparisons
                    if pf_folder == 'search_history':
                        for directness in ['direct']:
                            pf_values = [pf for pf in scores_by_pf.keys() if pf[0] == directness]
                            scores_list = [scores_by_pf[pf] for pf in pf_values]
                            scores_list = ensure_numeric(scores_list)
                            # print(f"Performing tests for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}, {pf_values}")
                            # print(f"scores_list: {len(scores_list)}")
                            # print("shape scores_list", [scores.shape for scores in scores_list])
                            # print('scores_list', scores_list)
                            num_comparisons = len(scores_list) * (len(scores_list) - 1) / 2
                            # print(f"num_comparisons: {num_comparisons}")
                            if len(scores_list) == 0:
                                print(f"No data for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name} {pf_values}")
                            elif len(scores_list) == 1:
                                print(f"Only one group for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}. Cannot perform statistical test.")
                                # 통계 테스트를 할 수 없는 경우 기본값 설정
                                key = (datetime_folder, pir_folder, pf_folder, query, model_name, directness)
                                pf_model_comparisons[key] = {
                                    'pf_values': pf_values,
                                    'test': 'None',
                                    'stat': 0.0,
                                    'p_value': 1.0,
                                    'normality_passed': False,
                                    'homogeneity_passed': False,
                                    'tukey_results': None,
                                    'effect_size': 0.0,
                                    'effect_size_type': 'None',
                                    'effect_size_secondary': 0.0,
                                    'effect_size_secondary_type': 'None',
                                    'effect_interpretation': 'negligible'
                                }
                            elif len(scores_list) > 1:
                                try:
                                    normality_passed = all(shapiro(scores)[1] >= 0.05 for scores in scores_list)
                                    homogeneity_passed = levene(*scores_list)[1] >= 0.05

                                    # 전체 샘플 수 계산
                                    n_total = sum(len(group) for group in scores_list)
                                    # print(f"n_total: {n_total}")
                                    n_groups = len(scores_list)

                                    if normality_passed and homogeneity_passed:
                                        try:
                                            stat, p_value = f_oneway(*scores_list)
                                            # NaN 확인 및 처리
                                            if np.isnan(stat) or np.isnan(p_value):
                                                
                                                print(f"Warning: NaN result in ANOVA for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}")
                                                print("scores_list",scores_list)
                                                stat = 0.0
                                                p_value = 1.0  # 가장 보수적인 값
                                            
                                            test_name = 'ANOVA'
                                            try:
                                                tukey_results = pairwise_tukeyhsd(np.concatenate(scores_list), np.concatenate([[i]*len(scores) for i, scores in enumerate(scores_list)]))
                                            except Exception as e:
                                                print(f"Error in Tukey test: {e}")
                                                tukey_results = None
                                            
                                            # ANOVA effect size 계산
                                            eta_squared, omega_squared, effect_interpretation = calculate_anova_effect_size(scores_list)
                                            effect_size = eta_squared
                                            effect_size_type = 'Eta Squared'
                                            effect_size_secondary = omega_squared
                                            effect_size_secondary_type = 'Omega Squared'
                                        except Exception as e:
                                            print(f"Error in ANOVA: {e}")
                                            stat = 0.0
                                            p_value = 1.0  # 가장 보수적인 값
                                            test_name = 'ANOVA (Error)'
                                            tukey_results = None
                                            effect_size = 0.0
                                            effect_size_type = 'Eta Squared'
                                            effect_size_secondary = 0.0
                                            effect_size_secondary_type = 'Omega Squared'
                                            effect_interpretation = 'negligible'
                                    else:
                                        try:
                                            stat, p_value = kruskal(*scores_list)
                                            # NaN 확인 및 처리
                                            if np.isnan(stat) or np.isnan(p_value):
                                                print(f"Warning: NaN result in Kruskal-Wallis for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}")
                                                stat = 0.0
                                                p_value = 1.0  # 가장 보수적인 값
                                            
                                            # print(f"Original p-values: {p_value}")  # Kruskal-Wallis 테스트 결과 출력
                                            test_name = 'Kruskal-Wallis'
                                            tukey_results = None
                                            
                                            # Kruskal-Wallis effect size 계산
                                            eta_squared, epsilon_squared, effect_interpretation = calculate_kruskal_effect_size(stat, n_total, n_groups)
                                            effect_size = eta_squared
                                            effect_size_type = 'Eta Squared'
                                            effect_size_secondary = epsilon_squared
                                            effect_size_secondary_type = 'Epsilon Squared'
                                        except Exception as e:
                                            print(f"Error in Kruskal-Wallis: {e}")
                                            stat = 0.0
                                            p_value = 1.0  # 가장 보수적인 값
                                            test_name = 'Kruskal-Wallis (Error)'
                                            tukey_results = None
                                            effect_size = 0.0
                                            effect_size_type = 'Eta Squared'
                                            effect_size_secondary = 0.0
                                            effect_size_secondary_type = 'Epsilon Squared'
                                            effect_interpretation = 'negligible'
                                except Exception as e:
                                    print(f"Error during statistical tests: {e}")
                                    # 오류 발생 시 기본값 설정
                                    normality_passed = False
                                    homogeneity_passed = False
                                    stat = 0.0
                                    p_value = 1.0
                                    test_name = 'Error'
                                    tukey_results = None
                                    effect_size = 0.0
                                    effect_size_type = 'None'
                                    effect_size_secondary = 0.0
                                    effect_size_secondary_type = 'None'
                                    effect_interpretation = 'negligible'

                                key = (datetime_folder, pir_folder, pf_folder, query, model_name, directness)
                                pf_model_comparisons[key] = {
                                    'pf_values': pf_values,
                                    'test': test_name,
                                    'stat': stat,
                                    'p_value': p_value,
                                    'normality_passed': normality_passed,
                                    'homogeneity_passed': homogeneity_passed,
                                    'tukey_results': tukey_results,
                                    'effect_size': effect_size,
                                    'effect_size_type': effect_size_type,
                                    'effect_size_secondary': effect_size_secondary,
                                    'effect_size_secondary_type': effect_size_secondary_type,
                                    'effect_interpretation': effect_interpretation
                                }
                    else:
                        # Handling non-search_history folders
                        pf_values = list(scores_by_pf.keys())
                        scores_list = [scores_by_pf[pf] for pf in pf_values]
                        scores_list = ensure_numeric(scores_list)
                        # for scores in scores_list:
                        #     print(f"Contains NaN: {np.isnan(scores).any()}")
                        # print(f"Performing tests for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name} {pf_values}")
                        # print("scores_list", scores_list)
                        # print(f"scores_list: {len(scores_list)}")
                        # print("shape scores_list", [scores.shape for scores in scores_list])
                        num_comparisons = len(scores_list) * (len(scores_list) - 1) / 2
                        # print(f"num_comparisons: {num_comparisons}")
                        if len(scores_list) == 0:
                            print(f"No data for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name} {pf_values}")
                        elif len(scores_list) == 1:
                            print(f"Only one group for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}. Cannot perform statistical test.")
                            # 통계 테스트를 할 수 없는 경우 기본값 설정
                            key = (datetime_folder, pir_folder, pf_folder, query, model_name, 'all')
                            pf_model_comparisons[key] = {
                                'pf_values': pf_values,
                                'test': 'None',
                                'stat': 0.0,
                                'p_value': 1.0,
                                'normality_passed': False,
                                'homogeneity_passed': False,
                                'tukey_results': None,
                                'effect_size': 0.0,
                                'effect_size_type': 'None',
                                'effect_size_secondary': 0.0,
                                'effect_size_secondary_type': 'None',
                                'effect_interpretation': 'negligible'
                            }
                        elif len(scores_list) > 1:
                            try:
                                normality_passed = all(shapiro(scores)[1] >= 0.05 for scores in scores_list)
                                homogeneity_passed = levene(*scores_list)[1] >= 0.05

                                # 전체 샘플 수 계산
                                n_total = sum(len(group) for group in scores_list)
                                # print(f"n_total: {n_total}")
                                n_groups = len(scores_list)

                                if normality_passed and homogeneity_passed:
                                    try:
                                        stat, p_value = f_oneway(*scores_list)
                                        # NaN 확인 및 처리
                                        if np.isnan(stat) or np.isnan(p_value):
                                            print(f"Warning: NaN result in ANOVA for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}")
                                            # print("scores_list",scores_list)
                                            stat = 0.0
                                            p_value = 1.0  # 가장 보수적인 값
                                        
                                        test_name = 'ANOVA'
                                        try:
                                            tukey_results = pairwise_tukeyhsd(np.concatenate(scores_list), np.concatenate([[i]*len(scores) for i, scores in enumerate(scores_list)]))
                                        except Exception as e:
                                            print(f"Error in Tukey test: {e}")
                                            tukey_results = None
                                        
                                        # ANOVA effect size 계산
                                        eta_squared, omega_squared, effect_interpretation = calculate_anova_effect_size(scores_list)
                                        effect_size = eta_squared
                                        effect_size_type = 'Eta Squared'
                                        effect_size_secondary = omega_squared
                                        effect_size_secondary_type = 'Omega Squared'
                                    except Exception as e:
                                        print(f"Error in ANOVA: {e}")
                                        stat = 0.0
                                        p_value = 1.0  # 가장 보수적인 값
                                        test_name = 'ANOVA (Error)'
                                        tukey_results = None
                                        effect_size = 0.0
                                        effect_size_type = 'Eta Squared'
                                        effect_size_secondary = 0.0
                                        effect_size_secondary_type = 'Omega Squared'
                                        effect_interpretation = 'negligible'
                                else:
                                    try:
                                        stat, p_value = kruskal(*scores_list)
                                        # NaN 확인 및 처리
                                        if np.isnan(stat) or np.isnan(p_value):
                                            print(f"Warning: NaN result in Kruskal-Wallis for {datetime_folder}, {pir_folder}, {pf_folder}, {query}, {model_name}")
                                            stat = 0.0
                                            p_value = 1.0  # 가장 보수적인 값
                                        
                                        # print(f"Kruskal-Wallis Original p-values: {p_value}")  # Kruskal-Wallis 테스트 결과 출력
                                        test_name = 'Kruskal-Wallis'
                                        tukey_results = None
                                        
                                        # Kruskal-Wallis effect size 계산
                                        eta_squared, epsilon_squared, effect_interpretation = calculate_kruskal_effect_size(stat, n_total, n_groups)
                                        effect_size = eta_squared
                                        effect_size_type = 'Eta Squared'
                                        effect_size_secondary = epsilon_squared
                                        effect_size_secondary_type = 'Epsilon Squared'
                                    except Exception as e:
                                        print(f"Error in Kruskal-Wallis: {e}")
                                        stat = 0.0
                                        p_value = 1.0  # 가장 보수적인 값
                                        test_name = 'Kruskal-Wallis (Error)'
                                        tukey_results = None
                                        effect_size = 0.0
                                        effect_size_type = 'Eta Squared'
                                        effect_size_secondary = 0.0
                                        effect_size_secondary_type = 'Epsilon Squared'
                                        effect_interpretation = 'negligible'
                            except Exception as e:
                                print(f"Error during statistical tests: {e}")
                                # 오류 발생 시 기본값 설정
                                normality_passed = False
                                homogeneity_passed = False
                                stat = 0.0
                                p_value = 1.0
                                test_name = 'Error'
                                tukey_results = None
                                effect_size = 0.0
                                effect_size_type = 'None'
                                effect_size_secondary = 0.0
                                effect_size_secondary_type = 'None'
                                effect_interpretation = 'negligible'

                            key = (datetime_folder, pir_folder, pf_folder, query, model_name, 'all')
                            pf_model_comparisons[key] = {
                                'pf_values': pf_values,
                                'test': test_name,
                                'stat': stat,
                                'p_value': p_value,
                                'normality_passed': normality_passed,
                                'homogeneity_passed': homogeneity_passed,
                                'tukey_results': tukey_results,
                                'effect_size': effect_size,
                                'effect_size_type': effect_size_type,
                                'effect_size_secondary': effect_size_secondary,
                                'effect_size_secondary_type': effect_size_secondary_type,
                                'effect_interpretation': effect_interpretation
                            }

# NaN 값 확인
nan_keys = []
for key, info in pf_model_comparisons.items():
    if 'p_value' not in info or np.isnan(info.get('p_value', np.nan)):
        nan_keys.append(key)
        # 기본값 설정
        pf_model_comparisons[key]['p_value'] = 1.0

if nan_keys:
    print(f"Found {len(nan_keys)} keys with missing or NaN p_value before applying corrections")

# 본페로니 및 Benjamini-Hochberg 보정 적용
try:
    pf_model_comparisons = apply_corrections(pf_model_comparisons)
except Exception as e:
    print(f"Error during apply_corrections: {e}")
    # 수동으로 보정 적용
    for key, info in pf_model_comparisons.items():
        if 'p_value' in info:
            p_value = info['p_value']
            if np.isnan(p_value):
                p_value = 1.0
            pf_model_comparisons[key]['bonferroni_p_value'] = min(p_value * 1.0, 1.0)  # 단일 보정 적용
            pf_model_comparisons[key]['bh_adjusted_p_value'] = min(p_value * 1.0, 1.0)  # 단일 보정 적용
            pf_model_comparisons[key]['bonferroni_significant'] = False
            pf_model_comparisons[key]['bh_significant'] = False
            pf_model_comparisons[key]['correction_group'] = "manual_correction"
            pf_model_comparisons[key]['group_size'] = 1

# NaN 값 재확인
nan_keys = []
for key, info in pf_model_comparisons.items():
    missing_fields = []
    for field in ['p_value', 'bonferroni_p_value', 'bh_adjusted_p_value']:
        if field not in info or np.isnan(info.get(field, np.nan)):
            missing_fields.append(field)
    
    if missing_fields:
        nan_keys.append((key, missing_fields))
        # 기본값 설정
        for field in missing_fields:
            pf_model_comparisons[key][field] = 1.0
        
        # 관련 significant 필드 설정
        if 'bonferroni_p_value' in missing_fields:
            pf_model_comparisons[key]['bonferroni_significant'] = False
        if 'bh_adjusted_p_value' in missing_fields:
            pf_model_comparisons[key]['bh_significant'] = False

if nan_keys:
    print(f"Found {len(nan_keys)} keys with missing or NaN values after applying corrections")

# Save the results에서 DataFrame 생성 부분을 수정
try:
    results_df = pd.DataFrame([
        {
            'datetime_folder': key[0],
            'pir_folder': key[1],
            'pf_folder': key[2],
            'query': key[3].lower(),  # 쿼리를 소문자로 변환하여 unique_url_counts_df와 일치시킴
            'model_name': key[4],
            'directness': key[5],
            'pf_values': ', '.join(map(str, test_info.get('pf_values', []))),
            'test': test_info.get('test', 'None'),
            'stat': test_info.get('stat', 0.0),
            'p_value': test_info.get('p_value', 1.0),
            'bonferroni_p_value': test_info.get('bonferroni_p_value', 1.0),
            'bh_adjusted_p_value': test_info.get('bh_adjusted_p_value', 1.0),
            'original_significant': test_info.get('p_value', 1.0) < 0.05,
            'bonferroni_significant': test_info.get('bonferroni_significant', False),
            'bh_significant': test_info.get('bh_significant', False),
            'correction_group': test_info.get('correction_group', 'unknown'),
            'group_size': test_info.get('group_size', 0),
            'effect_size': test_info.get('effect_size', 0.0),
            'effect_size_type': test_info.get('effect_size_type', 'None'),
            'effect_size_secondary': test_info.get('effect_size_secondary', 0.0),
            'effect_size_secondary_type': test_info.get('effect_size_secondary_type', 'None'),
            'effect_interpretation': test_info.get('effect_interpretation', 'negligible'),
            'normality_passed': test_info.get('normality_passed', False),
            'homogeneity_passed': test_info.get('homogeneity_passed', False),
            'tukey_results': str(test_info.get('tukey_results', 'N/A'))
        }
        for key, test_info in pf_model_comparisons.items()
    ])
except Exception as e:
    print(f"Error creating results DataFrame: {e}")
    # 더 안전한 방식으로 DataFrame 생성
    rows = []
    for key, test_info in pf_model_comparisons.items():
        try:
            row = {
                'datetime_folder': key[0],
                'pir_folder': key[1],
                'pf_folder': key[2],
                'query': key[3].lower(),
                'model_name': key[4],
                'directness': key[5],
                'pf_values': ', '.join(map(str, test_info.get('pf_values', []))),
                'test': test_info.get('test', 'None'),
                'stat': test_info.get('stat', 0.0),
                'p_value': test_info.get('p_value', 1.0),
                'bonferroni_p_value': test_info.get('bonferroni_p_value', 1.0),
                'bh_adjusted_p_value': test_info.get('bh_adjusted_p_value', 1.0),
                'original_significant': test_info.get('p_value', 1.0) < 0.05,
                'bonferroni_significant': test_info.get('bonferroni_significant', False),
                'bh_significant': test_info.get('bh_significant', False),
                'correction_group': test_info.get('correction_group', 'unknown'),
                'group_size': test_info.get('group_size', 0),
                'effect_size': test_info.get('effect_size', 0.0),
                'effect_size_type': test_info.get('effect_size_type', 'None'),
                'effect_size_secondary': test_info.get('effect_size_secondary', 0.0),
                'effect_size_secondary_type': test_info.get('effect_size_secondary_type', 'None'),
                'effect_interpretation': test_info.get('effect_interpretation', 'negligible'),
                'normality_passed': test_info.get('normality_passed', False),
                'homogeneity_passed': test_info.get('homogeneity_passed', False),
                'tukey_results': str(test_info.get('tukey_results', 'N/A'))
            }
            rows.append(row)
        except Exception as e2:
            print(f"Error processing row {key}: {e2}")
    
    results_df = pd.DataFrame(rows)

# NaN 값 최종 확인 및 수정
for column in results_df.columns:
    nan_count = results_df[column].isna().sum()
    if nan_count > 0:
        print(f"Column {column} has {nan_count} NaN values. Filling with appropriate defaults.")
        
        # 데이터 타입에 따라 적절한 기본값 설정
        if column in ['p_value', 'bonferroni_p_value', 'bh_adjusted_p_value', 'stat', 'effect_size', 'effect_size_secondary', 'group_size']:
            results_df[column] = results_df[column].fillna(0.0 if column == 'stat' else 1.0)
        elif column in ['original_significant', 'bonferroni_significant', 'bh_significant', 'normality_passed', 'homogeneity_passed']:
            results_df[column] = results_df[column].fillna(False)
        elif column in ['test', 'effect_size_type', 'effect_size_secondary_type', 'effect_interpretation', 'correction_group']:
            results_df[column] = results_df[column].fillna('None')
        else:
            results_df[column] = results_df[column].fillna('')

# 고유 URL 개수 정보와 테스트 결과 병합
try:
    merged_results_df = pd.merge(
        results_df,
        unique_url_counts_df,
        on=['datetime_folder', 'pir_folder', 'pf_folder', 'query'],
        how='left'
    )
    
    # 병합 후 누락된 값 확인
    na_count = merged_results_df['Unique_URL_Count'].isna().sum()
    if na_count > 0:
        print(f"Warning: {na_count} rows have missing Unique_URL_Count after merge. Filling with 0.")
        merged_results_df['Unique_URL_Count'] = merged_results_df['Unique_URL_Count'].fillna(0)
except Exception as e:
    print(f"Error during merge with unique_url_counts_df: {e}")
    merged_results_df = results_df
    merged_results_df['Unique_URL_Count'] = 0  # 기본값 추가

# 결과 파일 저장
if not os.path.exists(os.path.join(current_dir, f'4')):
    os.makedirs(os.path.join(current_dir, f'4'))

try:
    merged_results_df.to_csv(f'4/tests_{setting_date}.csv', index=False)
    print(f"Results with unique URL counts saved to 'tests_{setting_date}.csv'")
except Exception as e:
    print(f"Error saving CSV file: {e}")
    # CSV 저장 실패 시 백업 파일 시도
    try:
        merged_results_df.to_csv(f'4/tests_{setting_date}_backup.csv', index=False)
        print(f"Backup results saved to 'tests_{setting_date}_backup.csv'")
    except Exception as e2:
        print(f"Error saving backup CSV file: {e2}")