"""
LLM Persona-based Data Analysis Module

This module analyzes news articles using multiple Large Language Models (LLMs) 
with different political personas to evaluate bias and stance in search results.
It processes data collected by the Context-Aware Concurrent Data Collection module
and applies various LLM models (ChatGPT, Claude) with different perspective prompts.

Key Features:
- Multi-model analysis (ChatGPT, Claude)
- Multiple persona perspectives (opposed/supportive, left/right)
- Result caching for efficiency
- Robust error handling and retry mechanisms
- Structured output format for further analysis

Author: Research Team
Date: 2024
"""

import os
import pandas as pd
from datetime import datetime
import time
import random
import re
import json

# Get the list of folders in the datasets directory
current_dir = os.path.dirname(os.path.abspath(__file__))
datasets_file_path = os.path.join(current_dir, '../datasets')
datetime_folders = [folder for folder in os.listdir(datasets_file_path) if os.path.isdir(os.path.join(datasets_file_path, folder))]

# Cache dictionary to store results based on model_version and URL
results_cache = {}

def load_existing_results(results_folder):
    """
    Load existing analysis results from CSV files to populate cache.
    
    This function scans the results directory for existing CSV files and loads
    the analysis results into the results_cache dictionary to avoid reprocessing
    articles that have already been analyzed.
    
    Args:
        results_folder (str): Path to the folder containing result CSV files
    """
    for root, dirs, files in os.walk(results_folder):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                df = pd.read_csv(file_path)
                for model_version in df.columns:
                    if model_version not in ['page', 'rank', 'source', 'title', 'content', 'url', 'Article_Content']:
                        if model_version not in results_cache:
                            results_cache[model_version] = {}
                        for _, row in df.iterrows():
                            if pd.notna(row[model_version]) and row[model_version] != "":
                                results_cache[model_version][row['url']] = row[model_version]
    print(f"Loaded {sum(len(model_cache) for model_cache in results_cache.values())} cached results.")
    for model_version, model_cache in results_cache.items():
        print(f"{model_version}: {len(model_cache)} cached results")


def create_chatgpt_content(query, title, text, chatgpt_model_version_list):
    """
    Generate ChatGPT analysis responses for different personas.
    
    This function creates analysis responses using ChatGPT models with different
    political personas (opposed/supportive, left/right) for a given article.
    
    Args:
        query (str): The search query used to find the article
        title (str): The article title
        text (str): The article content
        chatgpt_model_version_list (list): List of ChatGPT model versions to use
        
    Returns:
        dict: Dictionary containing responses for each model-persona combination
    """
    responses = {}
    role_prompts = {
        'opp_left': create_role_opposed_left_prompt(query),
        'opp_right': create_role_opposed_right_prompt(query),
        'sup_left': create_role_supportive_left_prompt(query),
        'sup_right': create_role_supportive_right_prompt(query)
    }
    content_prompt = create_content_prompt(query, title, text)
    
    for model_version in chatgpt_model_version_list:
        from chatgpt.chatgpt_request import ChatGPT
        print(f"Processing ChatGPT model version: {model_version}")
        
        for persona, role_prompt in role_prompts.items():
            model_persona_key = f"{model_version}_{persona}"
            print(f"Processing persona: {persona}")
            
            chatgpt = ChatGPT(model_version)
            chatgpt.add_role(role_prompt)
            response = chatgpt.run(content_prompt)
            responses[model_persona_key] = response if response else create_empty_result_json()
            
            # Add delay between requests to avoid rate limiting
            time.sleep(random.uniform(1, 3))
    
    return responses


def create_claude_content(query, title, text, claude_model_version_list):
    """
    Generate Claude analysis responses for different personas.
    
    This function creates analysis responses using Claude models with different
    political personas (opposed/supportive, left/right) for a given article.
    
    Args:
        query (str): The search query used to find the article
        title (str): The article title
        text (str): The article content
        claude_model_version_list (list): List of Claude model versions to use
        
    Returns:
        dict: Dictionary containing responses for each model-persona combination
    """
    responses = {}
    role_prompts = {
        'opp_left': create_role_opposed_left_prompt(query),
        'opp_right': create_role_opposed_right_prompt(query),
        'sup_left': create_role_supportive_left_prompt(query),
        'sup_right': create_role_supportive_right_prompt(query)
    }
    content_prompt = create_content_prompt(query, title, text)
    
    for model_version in claude_model_version_list:
        from claude.claude_request import Claude
        print(f"Processing Claude model version: {model_version}")
        
        for persona, role_prompt in role_prompts.items():
            model_persona_key = f"{model_version}_{persona}"
            print(f"Processing persona: {persona}")
            
            claude = Claude(model_version)
            claude.add_role(role_prompt)
            response = claude.run(content_prompt)
            responses[model_persona_key] = response if response else create_empty_result_json()
            
            # Add delay between requests to avoid rate limiting
            time.sleep(random.uniform(1, 3))
    
    return responses

def create_role_opposed_left_prompt(query):
    """
    Create a left-leaning opposed perspective prompt.
    
    Args:
        query (str): The search query to incorporate into the prompt
        
    Returns:
        str: Formatted prompt for left-leaning opposed perspective
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file_path = os.path.join(current_dir, 'prompt', 'prompt_role_opposed_left.txt')
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        prompt_template = file.read()
    return prompt_template.format(query=query)


def create_role_opposed_right_prompt(query):
    """
    Create a right-leaning opposed perspective prompt.
    
    Args:
        query (str): The search query to incorporate into the prompt
        
    Returns:
        str: Formatted prompt for right-leaning opposed perspective
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file_path = os.path.join(current_dir, 'prompt', 'prompt_role_opposed_right.txt')
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        prompt_template = file.read()
    return prompt_template.format(query=query)


def create_role_supportive_left_prompt(query):
    """
    Create a left-leaning supportive perspective prompt.
    
    Args:
        query (str): The search query to incorporate into the prompt
        
    Returns:
        str: Formatted prompt for left-leaning supportive perspective
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file_path = os.path.join(current_dir, 'prompt', 'prompt_role_supportive_left.txt')
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        prompt_template = file.read()
    return prompt_template.format(query=query)


def create_role_supportive_right_prompt(query):
    """
    Create a right-leaning supportive perspective prompt.
    
    Args:
        query (str): The search query to incorporate into the prompt
        
    Returns:
        str: Formatted prompt for right-leaning supportive perspective
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file_path = os.path.join(current_dir, 'prompt', 'prompt_role_supportive_right.txt')
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        prompt_template = file.read()
    return prompt_template.format(query=query)


def create_content_prompt(query, title, text):
    """
    Create a content analysis prompt with article details.
    
    Args:
        query (str): The search query used to find the article
        title (str): The article title
        text (str): The article content
        
    Returns:
        str: Formatted content analysis prompt
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file_path = os.path.join(current_dir, 'prompt', 'prompt_content.txt')
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        prompt_template = file.read()
    return prompt_template.format(query=query, title=title, text=text)


def create_empty_result_json():
    """
    Create an empty result JSON structure for failed API calls.
    
    Returns:
        str: JSON string with empty analysis structure
    """
    empty_result = {
        "Political": {
            "label": None,
            "score": None
        },
        "Stance": {
            "label": None,
            "score": None
        },
        "Reasoning": None
    }
    return json.dumps(empty_result)

def get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list, endswith_date):
    """
    Main processing function for analyzing datasets within a date range.
    
    This function iterates through collected datasets, applies LLM analysis with
    multiple personas, and saves the results with proper caching.
    
    Args:
        datetime_range (list): List containing [start_date, end_date] in 'YYYY-MM-DD' format
        claude_model_version_list (list): List of Claude model versions to use
        chatgpt_model_version_list (list): List of ChatGPT model versions to use
        endswith_date (str): Suffix for result folder naming
    """
    personas = ['opp_left', 'opp_right', 'sup_left', 'sup_right']
    start_date = datetime.strptime(datetime_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(datetime_range[1], "%Y-%m-%d")
    
    # Load existing results to populate cache
    results_folder = os.path.join(current_dir, f'../result_folder/results_{endswith_date}')
    if os.path.exists(results_folder):
        load_existing_results(results_folder)
    
    # Process each date folder within range
    datetime_folders = sorted([folder for folder in os.listdir(datasets_file_path) 
                              if os.path.isdir(os.path.join(datasets_file_path, folder))])
    
    for datetime_folder in datetime_folders:
        try:
            folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
            if folder_date < start_date or folder_date > end_date:
                print(f"Skipping folder: {datetime_folder} (outside date range)")
                continue
        except ValueError:
            print(f"Skipping invalid date folder: {datetime_folder}")
            continue
        
        print(f"\nProcessing date folder: {datetime_folder}")
        process_date_folder(datetime_folder, claude_model_version_list, chatgpt_model_version_list, 
                           endswith_date, personas)


def process_date_folder(datetime_folder, claude_model_version_list, chatgpt_model_version_list, 
                       endswith_date, personas):
    """
    Process all data files within a specific date folder.
    
    Args:
        datetime_folder (str): Date folder name (YYYY-MM-DD format)
        claude_model_version_list (list): List of Claude model versions
        chatgpt_model_version_list (list): List of ChatGPT model versions
        endswith_date (str): Suffix for result folder naming
        personas (list): List of persona types to process
    """
    pir_path = os.path.join(datasets_file_path, datetime_folder)
    pir_folders = sorted([folder for folder in os.listdir(pir_path) 
                         if os.path.isdir(os.path.join(pir_path, folder))])

    for pir_folder in pir_folders:
        pf_path = os.path.join(pir_path, pir_folder)
        pf_folders = sorted([folder for folder in os.listdir(pf_path) 
                            if os.path.isdir(os.path.join(pf_path, folder))])
        
        for pf_folder in pf_folders:
            final_path = os.path.join(pf_path, pf_folder)
            csv_files = sorted([file for file in os.listdir(final_path) 
                               if file.endswith('.csv')])
            
            for file in csv_files:
                dataset_file_path = os.path.join(final_path, file)
                process_single_file(dataset_file_path, file, datetime_folder, pir_folder, pf_folder,
                                   claude_model_version_list, chatgpt_model_version_list, 
                                   endswith_date, personas)


def process_single_file(dataset_file_path, file, datetime_folder, pir_folder, pf_folder,
                       claude_model_version_list, chatgpt_model_version_list, endswith_date, personas):
    """
    Process a single CSV file with LLM analysis.
    
    Args:
        dataset_file_path (str): Path to the CSV file
        file (str): Filename
        datetime_folder (str): Date folder name
        pir_folder (str): PIR folder name  
        pf_folder (str): PF folder name
        claude_model_version_list (list): Claude model versions
        chatgpt_model_version_list (list): ChatGPT model versions
        endswith_date (str): Result folder suffix
        personas (list): Persona types
    """
    try:
        df = pd.read_csv(dataset_file_path)
        print(f"Loaded dataset: {dataset_file_path} ({len(df)} articles)")
        
        if 'Article_Content' not in df.columns:
            print(f"Skipping {file}: Missing 'Article_Content' column")
            return
        
        # Extract query information
        file_name = file.replace('.csv', '')
        query_parts = file_name.split('_')
        query = query_parts[0] if query_parts else "unknown"
        pf = query_parts[1:] if len(query_parts) > 1 else []
        
        print(f"Processing: Date={datetime_folder}, PIR={pir_folder}, PF={pf_folder}, Query={query}, PF Details={pf}")

        # Prepare result file path
        result_final_path = final_path.replace('../datasets', f'../result_folder/results_{endswith_date}')
        result_file_path = os.path.join(result_final_path, file)
        os.makedirs(result_final_path, exist_ok=True)

        # Load existing result file if it exists
        existing_columns = set()
        if os.path.exists(result_file_path):
            existing_df = pd.read_csv(result_file_path)
            for col in existing_df.columns:
                if col not in ['page', 'rank', 'source', 'title', 'content', 'url', 'Article_Content']:
                    df[col] = existing_df[col]
                    existing_columns.add(col)
        
        # Initialize only necessary new columns
        all_model_versions = chatgpt_model_version_list + claude_model_version_list
        for model_version in all_model_versions:
            for persona in personas:
                model_persona_key = f"{model_version}_{persona}"
                if model_persona_key not in existing_columns:
                    df[model_persona_key] = ""
                # Initialize cache dictionary
                if model_persona_key not in results_cache:
                    results_cache[model_persona_key] = {}

        # Set to track processing status by URL
        processed_urls = set()

        # Process each article
        for i, (url, title, text) in enumerate(zip(df['url'].tolist(), df['title'].tolist(), df['Article_Content'].tolist())):
            print(f"\nProcessing article {i+1}/{len(df)}")
            row_updated = False

            # Process each model type
            for model_list, create_func in [
                (chatgpt_model_version_list, create_chatgpt_content),
                (claude_model_version_list, create_claude_content)
            ]:
                for model_version in model_list:
                    responses_needed = False
                    for persona in personas:
                        model_persona_key = f"{model_version}_{persona}"
                        
                        # Check if URL is already in cache
                        if url in results_cache[model_persona_key]:
                            if pd.isna(df.at[i, model_persona_key]) or df.at[i, model_persona_key] == "":
                                print(f"Using cached result for {model_persona_key} and URL: {url}")
                                df.at[i, model_persona_key] = results_cache[model_persona_key][url]
                                row_updated = True
                        elif pd.isna(df.at[i, model_persona_key]) or df.at[i, model_persona_key] == "":
                            responses_needed = True
                            break
                    
                    # If responses are needed, call the API once for all personas
                    if responses_needed:
                        print(f"Generating new responses for {model_version}")
                        try:
                            responses = create_func(query, title, text, [model_version])
                            for persona in personas:
                                model_persona_key = f"{model_version}_{persona}"
                                if pd.isna(df.at[i, model_persona_key]) or df.at[i, model_persona_key] == "":
                                    response = responses[model_persona_key]
                                    df.at[i, model_persona_key] = response
                                    # Store new response in cache
                                    results_cache[model_persona_key][url] = response
                                    row_updated = True
                        except Exception as e:
                            print(f"Error processing {model_version}: {str(e)}")
                            continue

            # Save results after each article if updated
            if row_updated:
                df.to_csv(result_file_path, index=False)
                print(f"Updated results saved to {result_file_path}")
                
                # Print cache status
                print("\nCurrent cache status:")
                for model_version in all_model_versions:
                    for persona in personas:
                        model_persona_key = f"{model_version}_{persona}"
                        cache_count = len(results_cache[model_persona_key])
                        print(f"{model_persona_key}: {cache_count} cached results")

        print(f"Finished processing {result_file_path}\n{'-'*80}")
        
    except Exception as e:
        print(f"Error processing file {dataset_file_path}: {str(e)}")


if __name__ == '__main__':
    # Configuration
    claude_model_version_list = [
        'claude-3-5-sonnet-20241022'
    ]
    chatgpt_model_version_list = [
        'gpt-4o',
    ]
    datetime_range = ['2024-09-24', '2024-09-30']
    endswith_date = '0921-30'  # You can change this or use: datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    print("="*80)
    print("LLM PERSONA-BASED DATA ANALYSIS")
    print("="*80)
    print(f"Date range: {datetime_range[0]} to {datetime_range[1]}")
    print(f"Claude models: {claude_model_version_list}")
    print(f"ChatGPT models: {chatgpt_model_version_list}")
    print(f"Results suffix: {endswith_date}")
    print("="*80)

    # Execute analysis
    get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list, endswith_date)