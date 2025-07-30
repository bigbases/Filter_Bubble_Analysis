import os
import pandas as pd
from datetime import datetime
import time, random
import re

# Get the list of folders in the datasets directory
current_dir = os.path.dirname(os.path.abspath(__file__))
datasets_file_path = os.path.join(current_dir, '../datasets')
datetime_folders = [folder for folder in os.listdir(datasets_file_path) if os.path.isdir(os.path.join(datasets_file_path, folder))]

# Cache dictionary to store results based on model_version and URL
results_cache = {}

def load_existing_results(results_folder):
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
            print(f"ChatGPT ({model_persona_key}) Response: {response}")
            responses[model_persona_key] = response
            
    return responses

def create_claude_content(query, title, text, claude_model_version_list):
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
            print(f"Claude ({model_persona_key}) Response: {response}")
            responses[model_persona_key] = response
            
    return responses

def create_role_opposed_left_prompt(query):
    role_prompt_path = os.path.join(current_dir, 'prompt', 'prompt_role_opposed_left.txt')
    with open(role_prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template.format(query=query)

def create_role_opposed_right_prompt(query):
    role_prompt_path = os.path.join(current_dir, 'prompt', 'prompt_role_opposed_right.txt')
    with open(role_prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template.format(query=query)

def create_role_supportive_left_prompt(query):
    role_prompt_path = os.path.join(current_dir, 'prompt', 'prompt_role_supportive_left.txt')
    with open(role_prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template.format(query=query)

def create_role_supportive_right_prompt(query):
    role_prompt_path = os.path.join(current_dir, 'prompt', 'prompt_role_supportive_right.txt')
    with open(role_prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template.format(query=query)

def create_content_prompt(query, title, text):
    content_prompt_path = os.path.join(current_dir, 'prompt', 'prompt_content.txt')
    with open(content_prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template.format(query=query, title=title, text=text)

def create_empty_result_json():
    return """
    {
    "Political": {
        "label": "Undecided",
        "score": 0.0
    },
    "Stance": {
        "label": "Undecided",
        "score": 0.0
    },
    "Reasoning": ""
    }
    """

def get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list, endswith_date):
    start_date = datetime.strptime(datetime_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(datetime_range[1], "%Y-%m-%d")
    personas = ['opp_left', 'opp_right', 'sup_left', 'sup_right']

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

                    if query in ['Russia Ukraine', 'Trump harris', 'Israel hamas', 'Biden Trump', 'israel hamas', 'russia ukraine', 'trump harris']:
                        if len(query.split(' ')) > 0:
                            query = query.split(' ')[0]

                    pf = file_name.split('_')[1:]

                    print(f"Processing: Date={datetime_folder}, PIR={pir_folder}, PF={pf_folder}, Query={query}, PF Details={pf}")

                    # Prepare the result file path
                    result_final_path = final_path.replace('../datasets', f'../ result_folder/results_{endswith_date}')
                    result_file_path = os.path.join(result_final_path, file)
                    os.makedirs(result_final_path, exist_ok=True)

                    # 기존 결과 파일이 있다면 읽어오기
                    existing_columns = set()
                    if os.path.exists(result_file_path):
                        existing_df = pd.read_csv(result_file_path)
                        for col in existing_df.columns:
                            if col not in ['page', 'rank', 'source', 'title', 'content', 'url', 'Article_Content']:
                                df[col] = existing_df[col]
                                existing_columns.add(col)
                    
                    # 필요한 새 컬럼만 초기화
                    all_model_versions = chatgpt_model_version_list + claude_model_version_list
                    for model_version in all_model_versions:
                        for persona in personas:
                            model_persona_key = f"{model_version}_{persona}"
                            if model_persona_key not in existing_columns:
                                df[model_persona_key] = ""
                            # 캐시 딕셔너리 초기화
                            if model_persona_key not in results_cache:
                                results_cache[model_persona_key] = {}

                    # URL별 처리 현황을 추적하기 위한 세트
                    processed_urls = set()

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
                                    
                                    # URL이 이미 캐시에 있는지 확인
                                    if url in results_cache[model_persona_key]:
                                        if pd.isna(df.at[i, model_persona_key]) or df.at[i, model_persona_key] == "":
                                            print(f"Using cached result for {model_persona_key} and URL: {url}")
                                            df.at[i, model_persona_key] = results_cache[model_persona_key][url]
                                            row_updated = True
                                    elif pd.isna(df.at[i, model_persona_key]) or df.at[i, model_persona_key] == "":
                                        responses_needed = True

                                if responses_needed:
                                    if pd.isna(text) or not isinstance(text, str) or len(text.strip()) < 10:
                                        empty_result = create_empty_result_json()
                                        for persona in personas:
                                            model_persona_key = f"{model_version}_{persona}"
                                            df.at[i, model_persona_key] = empty_result
                                            results_cache[model_persona_key][url] = empty_result
                                            row_updated = True
                                    else:
                                        responses = create_func(query, title, text, [model_version])
                                        for persona in personas:
                                            model_persona_key = f"{model_version}_{persona}"
                                            if pd.isna(df.at[i, model_persona_key]) or df.at[i, model_persona_key] == "":
                                                response = responses[model_persona_key]
                                                df.at[i, model_persona_key] = response
                                                # 새로운 response를 캐시에 저장
                                                results_cache[model_persona_key][url] = response
                                                row_updated = True

                        if row_updated:
                            df.to_csv(result_file_path, index=False)
                            print(f"Updated results saved to {result_file_path}")
                            
                            # 캐시 상태 출력
                            print("\nCurrent cache status:")
                            for model_version in all_model_versions:
                                for persona in personas:
                                    model_persona_key = f"{model_version}_{persona}"
                                    cache_count = len(results_cache[model_persona_key])
                                    print(f"{model_persona_key}: {cache_count} cached results")

                    print(f"Finished processing {result_file_path}\n{'-'*80}")


if __name__ == '__main__':
    claude_model_version_list = [
        'claude-3-5-sonnet-20241022'
    ]
    chatgpt_model_version_list = [
        'gpt-4o',
    ]
    datetime_range = ['2024-09-24', '2024-09-30']
    endswith_date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    endswith_date = '0921-30'

    get_df(datetime_range, claude_model_version_list, chatgpt_model_version_list, endswith_date)