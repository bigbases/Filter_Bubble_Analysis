"""
Robust JSON Parsing Module

This module provides robust parsing capabilities for LLM responses.
It extracts and cleans JSON data from LLM outputs, handles various response formats,
and structures the data for analysis.

Key Features:
- Robust JSON extraction with multiple fallback methods
- Response format standardization
- Error handling for malformed responses
- Data validation and cleaning
- Support for multiple LLM response formats

Author: Research Team
Date: 2024
"""

import os
import json
import re
import pandas as pd
from datetime import datetime
from claude.claude_request import Claude
from chatgpt.chatgpt_request import ChatGPT

current_dir = os.path.dirname(os.path.abspath(__file__))
setting_date = '0921-30'
datasets_file_path = os.path.join(current_dir, f'../result_folder/results_{setting_date}')
results_file_path = os.path.join(current_dir, f'../result_folder/results_{setting_date}')
datetime_folders = [folder for folder in os.listdir(datasets_file_path) if os.path.isdir(os.path.join(datasets_file_path, folder))]

def get_model_persona_columns(df, model_version_list):
    """
    Get all columns that correspond to model versions with personas.
    
    Args:
        df (pd.DataFrame): The dataframe to check for columns
        model_version_list (list): List of model versions to check
        
    Returns:
        list: List of column names matching model-persona combinations
    """
    personas = ['opp_left', 'opp_right', 'sup_left', 'sup_right']
    columns = []
    for model_version in model_version_list:
        for persona in personas:
            column = f"{model_version}_{persona}"
            if column in df.columns:
                columns.append(column)
    return columns


def get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list):
    """
    Process and parse LLM analysis results from CSV files within date range.
    
    This function iterates through result files in the specified date range,
    extracts LLM responses, parses them into structured format, and saves
    the processed results.
    
    Args:
        datetime_range (list): List containing start and end dates [start_date, end_date]
        claude_model_version_list (list): List of Claude model versions to process
        chatgpt_model_version_list (list): List of ChatGPT model versions to process
    """
    start_date = datetime.strptime(datetime_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(datetime_range[1], "%Y-%m-%d")
    
    datetime_folders = sorted([folder for folder in os.listdir(datasets_file_path) 
                              if os.path.isdir(os.path.join(datasets_file_path, folder))])
    
    for datetime_folder in datetime_folders:
        folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
        if folder_date < start_date or folder_date > end_date:
            print(f"Skipping folder: {datetime_folder}")
            continue
        
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
                                  if file.endswith('.csv') and not file.startswith('finetune_classified_updated_')])
                
                for file in csv_files:
                    dataset_file_path = os.path.join(final_path, file)
                    process_csv_file(dataset_file_path, claude_model_version_list, chatgpt_model_version_list)


def process_csv_file(dataset_file_path, claude_model_version_list, chatgpt_model_version_list):
    """
    Process a single CSV file and parse LLM responses.
    
    Args:
        dataset_file_path (str): Path to the CSV file to process
        claude_model_version_list (list): List of Claude model versions
        chatgpt_model_version_list (list): List of ChatGPT model versions
    """
    if not os.path.exists(dataset_file_path):
        print(f"File does not exist: {dataset_file_path}")
        return
        
    print(f"Processing file: {dataset_file_path}")
    df = pd.read_csv(dataset_file_path)
    
    all_model_versions = claude_model_version_list + chatgpt_model_version_list
    model_persona_columns = get_model_persona_columns(df, all_model_versions)
    
    if not model_persona_columns:
        print(f"No model-persona columns found in {dataset_file_path}")
        return
    
    # Create new columns for parsed results
    for column in model_persona_columns:
        for field in ['Political_Label', 'Political_Score', 'Stance_Label', 'Stance_Score', 'Reasoning']:
            new_column_name = f"{column}_{field}"
            if new_column_name not in df.columns:
                df[new_column_name] = None
    
    # Process each row
    for index, row in df.iterrows():
        for column in model_persona_columns:
            raw_response = row[column]
            if pd.notna(raw_response) and raw_response != "":
                parsed_result = parse_response(raw_response)
                if parsed_result:
                    for field, value in parsed_result.items():
                        df.at[index, f"{column}_{field}"] = value
    
    # Save the updated dataframe
    output_path = dataset_file_path.replace('.csv', '_parsed.csv')
    df.to_csv(output_path, index=False)
    print(f"Parsed results saved to: {output_path}")


def clean_json_string(json_string):
    """
    Clean and prepare JSON string for parsing.
    
    Args:
        json_string (str): Raw JSON string from LLM response
        
    Returns:
        str or None: Cleaned JSON string or None if extraction failed
    """
    if not json_string or pd.isna(json_string):
        return None
    
    # Try to extract JSON from the response
    extracted_json = robust_json_extract(json_string)
    if not extracted_json:
        return None
    
    # Clean up common formatting issues
    cleaned = extracted_json.strip()
    cleaned = re.sub(r'\n\s*', ' ', cleaned)  # Remove newlines and extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)    # Normalize spaces
    
    return cleaned


def robust_json_extract(text):
    """
    Extract JSON from text using multiple strategies.
    
    Args:
        text (str): Text containing JSON response
        
    Returns:
        str or None: Extracted JSON string or None if not found
    """
    if not text:
        return None
    
    # Strategy 1: Look for complete JSON objects
    json_patterns = [
        r'\{[^{}]*"Political"[^{}]*"Stance"[^{}]*"Reasoning"[^{}]*\}',
        r'\{.*?"Political":.*?"Stance":.*?"Reasoning":.*?\}',
        r'\{.*?"Political":.*?"Bias":.*?\}',
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(0)
    
    return None


def parse_response(json_string):
    """
    Parse LLM response JSON into structured format.
    
    This function handles various response formats and extracts political
    analysis data including labels, scores, and reasoning.
    
    Args:
        json_string (str): JSON string from LLM response
        
    Returns:
        dict or None: Parsed analysis data or None if parsing failed
    """
    try:
        clean_string = clean_json_string(json_string)
        if not clean_string:
            return {
                'Political_Label': None,
                'Political_Score': None,
                'Stance_Label': None,
                'Stance_Score': None,
                'Reasoning': None,
            }

        try:
            data = json.loads(clean_string)
        except json.JSONDecodeError:
            # Fallback: Manual extraction using regex
            data = {}
            for field in ['Political', 'Stance']:
                label_match = re.search(fr'"{field}":\s*{{\s*"label":\s*"([^"]+)"', clean_string)
                score_match = re.search(fr'"{field}":\s*{{\s*"label":[^}}]+,"score":\s*([-]?\d+\.?\d*)', clean_string)
                data[field] = {
                    'label': label_match.group(1) if label_match else None,
                    'score': float(score_match.group(1)) if score_match else None
                }

            reasoning_match = re.search(r'"Reasoning":\s*"(.*?)"', clean_string, re.DOTALL)
            data['Reasoning'] = reasoning_match.group(1) if reasoning_match else None

        # Normalize "Neutral" to "Center" for consistency
        if data.get('Political', {}).get('label') == "Neutral":
            data['Political']['label'] = "Center"

        return {
            'Political_Label': data.get('Political', {}).get('label'),
            'Political_Score': data.get('Political', {}).get('score'),
            'Stance_Label': data.get('Stance', {}).get('label'),
            'Stance_Score': data.get('Stance', {}).get('score'),
            'Reasoning': data.get('Reasoning'),
        }
    
    except Exception as e:
        print(f"Error parsing JSON: {e}", json_string)
        return None


if __name__ == '__main__':
    claude_model_version_list = [
        'claude-3-5-sonnet-20241022'
    ]
    chatgpt_model_version_list = [
        'gpt-4o',
    ]
    datetime_range = ['2024-09-21', '2024-09-30']
    get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list)