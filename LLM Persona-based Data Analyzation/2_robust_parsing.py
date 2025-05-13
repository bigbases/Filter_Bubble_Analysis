import os, json, re
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
    """Get all columns that correspond to model versions with personas"""
    personas = ['opp_left', 'opp_right', 'sup_left', 'sup_right']
    columns = []
    for model_version in model_version_list:
        for persona in personas:
            column = f"{model_version}_{persona}"
            if column in df.columns:
                columns.append(column)
    return columns

def get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list):
    start_date = datetime.strptime(datetime_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(datetime_range[1], "%Y-%m-%d")
    
    datetime_folders = sorted([folder for folder in os.listdir(datasets_file_path) if os.path.isdir(os.path.join(datasets_file_path, folder))])
    for datetime_folder in datetime_folders:
        folder_date = datetime.strptime(datetime_folder, "%Y-%m-%d")
        if folder_date < start_date or folder_date > end_date:
            print(f"Skipping folder: {datetime_folder}")
            continue
        
        pir_path = os.path.join(datasets_file_path, datetime_folder)
        pir_folders = [folder for folder in os.listdir(pir_path) if os.path.isdir(os.path.join(pir_path, folder))]
        pir_folders = sorted(pir_folders)

        for pir_folder in pir_folders:
            pf_path = os.path.join(pir_path, pir_folder)
            pf_folders = [folder for folder in os.listdir(pf_path) if os.path.isdir(os.path.join(pf_path, folder))]
            pf_folders = sorted(pf_folders)
            
            for pf_folder in pf_folders:
                final_path = os.path.join(pf_path, pf_folder)
                csv_files = [file for file in os.listdir(final_path) if file.endswith('.csv') and not file.startswith('finetune_classified_updated_')]
                csv_files = sorted(csv_files)
                
                for file in csv_files:
                    dataset_file_path = os.path.join(final_path, file)
                    df = pd.read_csv(dataset_file_path)
                    print(f"Loaded dataset from {dataset_file_path}")
                    
                    file_name = file.replace('finetune_classified_updated_', '').replace('.csv', '')
                    query = file_name.split('_')[0]
                    pf = file_name.split('_')[1:]
                    
                    print(f"Processing: Date={datetime_folder}, PIR={pir_folder}, PF={pf_folder}, Query={query}, PF Details={pf}")

                    # Get columns for each model type with personas
                    claude_columns = get_model_persona_columns(df, claude_model_version_list)
                    chatgpt_columns = get_model_persona_columns(df, chatgpt_model_version_list)
                        
                    columns_to_process = claude_columns + chatgpt_columns

                    for column in columns_to_process:
                        print(f"Processing column: {column}")
                        # print(len(df[column]))
                        # print(df[column])
                        parsed_data = df[column].apply(parse_response)
                        
                        # Add persona information to the parsed data
                        model_name, persona = column.rsplit('_', 1)
                        parsed_df = pd.DataFrame(parsed_data.tolist())
                        
                        # Add persona information to column names
                        parsed_df = parsed_df.add_prefix(f'{column}_')
                        
                        # Add persona as a separate column
                        parsed_df[f'{column}_persona'] = persona
                        
                        # Concatenate with original DataFrame
                        df = pd.concat([df, parsed_df], axis=1)
                        # print(f"Processed column: {column}")
                        # print(df.head())
                    
                    # Save the updated DataFrame
                    result_final_path = final_path.replace('result_folder', 'parsing_folder')
                    result_file_path = os.path.join(result_final_path, file)
                    os.makedirs(result_final_path, exist_ok=True)
                    df.to_csv(result_file_path, index=False)
                    print(f"Saved updated results to {result_file_path}")

def clean_json_string(json_string):
    try:
        match = re.search(r'({.*?"Reasoning":.*?})\s*$', json_string, re.DOTALL)
        
        if match:
            json_part = match.group(1)
            json_part = re.sub(r'("Reasoning":\s*")(.+?)(")', 
                               lambda m: m.group(1) + re.sub(r'["\n]', '', m.group(2)) + m.group(3), 
                               json_part)
            return json_part
        else:
            match = re.search(r'({.*"Political":.*?"Bias":.*?}\s*})', json_string, re.DOTALL)
            return match.group(1) if match else None
    except Exception as e:
        print(f"Error cleaning JSON: {e}")
        return None

def robust_json_extract(text):
    try:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        return match.group(1) if match else None
    except Exception as e:
        print(f"Error cleaning JSON: {e}")
        return None

def parse_response(json_string):
    try:
        clean_string = clean_json_string(json_string)
        if not clean_string:
            return {
                'Political_Label': None,
                'Political_Score': None,
                'Stance_Label': None,
                'Stance_Score': None,
                # 'Sentiment_Label': None,
                # 'Sentiment_Score': None,
                'Subjectivity_Label': None,
                'Subjectivity_Score': None,
                'Bias_Label': None,
                'Bias_Score': None,
                'Reasoning': None,
            }

        try:
            data = json.loads(clean_string)
        except json.JSONDecodeError:
            data = {}
            for field in ['Political', 'Stance', 'Subjectivity', 'Bias']:
                label_match = re.search(fr'"{field}":\s*{{\s*"label":\s*"([^"]+)"', clean_string)
                score_match = re.search(fr'"{field}":\s*{{\s*"label":[^}}]+,"score":\s*([-]?\d+\.?\d*)', clean_string)
                data[field] = {
                    'label': label_match.group(1) if label_match else None,
                    'score': float(score_match.group(1)) if score_match else None
                }

            reasoning_match = re.search(r'"Reasoning":\s*"(.*?)"', clean_string, re.DOTALL)
            data['Reasoning'] = reasoning_match.group(1) if reasoning_match else None

        if data.get('Political', {}).get('label') == "Neutral":
            data['Political']['label'] = "Center"

        return {
            'Political_Label': data.get('Political', {}).get('label'),
            'Political_Score': data.get('Political', {}).get('score'),
            'Stance_Label': data.get('Stance', {}).get('label'),
            'Stance_Score': data.get('Stance', {}).get('score'),
            # 'Sentiment_Label': data.get('Sentiment', {}).get('label'),
            # 'Sentiment_Score': data.get('Sentiment', {}).get('score'),
            'Subjectivity_Label': data.get('Subjectivity', {}).get('label'),
            'Subjectivity_Score': data.get('Subjectivity', {}).get('score'),
            'Bias_Label': data.get('Bias', {}).get('label'),
            'Bias_Score': data.get('Bias', {}).get('score'),
            'Reasoning': data.get('Reasoning'),
        }
    
    except Exception as e:
        print(f"Error parsing JSON: {e}", json_string)
        return None


if __name__ == '__main__':
    claude_model_version_list = [
        # 'claude-3-opus-20240229',
        # 'claude-3-sonnet-20240229',
        # 'claude-3-haiku-20240307',
        'claude-3-5-sonnet-20241022'
    ]
    chatgpt_model_version_list = [
        'gpt-4o',
        # 'gpt-4o-mini',
        # 'gpt-4-turbo',
        # 'gpt-4',
        # 'gpt-3.5-turbo-0125',
        # 'chatgpt-4o-latest '
    ]
    datetime_range = ['2024-09-21', '2024-09-30']
    get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list)