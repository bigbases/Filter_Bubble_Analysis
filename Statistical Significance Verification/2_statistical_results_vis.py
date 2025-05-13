import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import math
import os

alpha_legend_data = {
    "Negligible (< 0.01)": 0.2,
    "Small (< 0.06)": 0.4,
    "Medium (< 0.14)": 0.7,
    "Large (≥ 0.14)": 1.0
}

def add_effectsize_alpha_legend(base_folder):
    fig, ax = plt.subplots(figsize=(2, 4))

    labels = list(alpha_legend_data.keys())
    alphas = list(alpha_legend_data.values())
    colors = ['#888888'] * len(alphas)

    for i, (label, alpha) in enumerate(zip(labels, alphas)):
        ax.scatter([0], [i], color=colors[i], alpha=alpha, s=400)
        ax.text(0.2, i, label, va='center', fontsize=12)

    ax.set_xlim(-0.5, 2)
    ax.set_ylim(-1, len(labels))
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(os.path.join(base_folder, "effect_size_alpha_legend.png"), dpi=600, bbox_inches='tight')
    plt.close()

def map_effect_alpha(effect_size):
    """효과 크기별로 투명도 조절"""
    if effect_size < 0.01:
        return 0.1
    elif effect_size < 0.06:
        return 0.3
    elif effect_size < 0.14:
        return 0.9
    else:
        return 1.0  # Large는 투명도는 그대로

def get_effect_color(effect_size):
    if effect_size >= 0.14:
        return '#C70039'  # 진한 빨간색
    else:
        return '#FF4500'  # 주황


def create_model_legend(df, base_folder='5_1'):
    import matplotlib.pyplot as plt
    import os

    fig, ax = plt.subplots(figsize=(10, 0.5))
    markers = ['8', '*']
    color = '#FF4500'

    df['model_name'] = df['model_name'].str.replace('_Score', '')
    model_labels = sorted(df['model_name'].unique())

    # 모델 마커
    for idx, model in enumerate(model_labels):
        ax.scatter([], [], marker=markers[idx % len(markers)],
                   color=color, s=250, label=model, edgecolor='none')

    # p-value 기준선
    ax.plot([], [], color='r', linestyle=':', label='Significance threshold (p = 0.05)')

    ax.axis('off')
    ax.legend(loc='center', ncol=3, fontsize=12, frameon=False, labelspacing=0.02,      # 세로 항목 간 간격 ↓
    handletextpad=0.3,     # 마커와 텍스트 간 거리 ↓
    borderaxespad=0.1,     # 레전드와 플롯 경계 거리 ↓
    borderpad=0.1          # 레전드 안쪽 패딩 ↓
    )
    
    path = os.path.join(base_folder, 'legend_models.png')
    plt.savefig(path, dpi=600, bbox_inches='tight', transparent=False)
    plt.close()

def create_effectsize_legend(base_folder='5_1'):
    import matplotlib.pyplot as plt
    import os

    alpha_legend_data = {
        "Negligible (< 0.01)": 0.1,
        "Small (< 0.06)": 0.3,
        "Medium (< 0.14)": 0.8,
        "Large (≥ 0.14)": 1.0
    }

    fig, ax = plt.subplots(figsize=(10, 0.5))
    # color = '#FF4500'
    colors = ['#FF4500', '#FF4500', '#FF4500', '#C70039']  # 마지막만 빨간색

    for i, (label, alpha) in enumerate(alpha_legend_data.items()):
        ax.scatter([], [], marker='o', color=colors[i], alpha=alpha, s=250, label=f"Effect: {label}", edgecolor='none')

    ax.axis('off')
    ax.legend(loc='center', ncol=4, fontsize=12, frameon=False, labelspacing=0.02,      # 세로 항목 간 간격 ↓
    handletextpad=0.3,     # 마커와 텍스트 간 거리 ↓
    borderaxespad=0.1,     # 레전드와 플롯 경계 거리 ↓
    borderpad=0.1          # 레전드 안쪽 패딩 ↓
    )
    
    path = os.path.join(base_folder, 'legend_effectsize.png')
    plt.savefig(path, dpi=600, bbox_inches='tight', transparent=False)
    plt.close()




def create_grid_plots(df, base_folder='5_1'):
    plt.rcParams['font.family'] = 'DeJavu Serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['font.size'] = 18  # Increase font size for better readability
    
    os.makedirs(base_folder, exist_ok=True)
    create_model_legend(df, base_folder)
    create_effectsize_legend(base_folder)
    
    
    # User Context 이름 매핑 및 순서 정의
    context_mapping = {
        'user_agent': 'E',
        'accept_language': 'L',
        'region': 'G',
        'search_history': 'S'
    }
    context_order = ['S', 'G', 'L', 'E']
    
    df['query'] = df['query'].str.upper()
    unique_queries = sorted(df['query'].unique())
    search_engines = sorted(df['pir_folder'].unique())
    
    markers = ['8', '*']  # Use consistent markers
    colors = ['#FF4500', '#FF4500']  # Complementary colors
    
    n_queries = len(unique_queries)
    n_cols = 3
    n_rows = math.ceil(n_queries / n_cols)
    
    # context 이름 매핑 적용
    df['pf_folder_mapped'] = df['pf_folder'].map(context_mapping)
    
    for search_engine in search_engines:
        fig = plt.figure(figsize=(18, 4*n_rows))  # 5*n_rows의 80%는 4*n_rows
        
        for idx, query in enumerate(unique_queries, 1):
            query_data = df[(df['query'] == query) & 
                          (df['pir_folder'] == search_engine)].copy()
            
            query_data['datetime_folder'] = pd.to_datetime(query_data['datetime_folder'])
            query_data = query_data.sort_values(['datetime_folder', 'pf_folder_mapped'])
            
            ax = fig.add_subplot(n_rows, n_cols, idx)
            
            unique_dates = sorted(query_data['datetime_folder'].unique())
            n_contexts = len(context_order)
            
            tick_positions = []
            tick_labels = []
            date_positions = []
            
            for date_idx, date in enumerate(unique_dates):
                base_pos = date_idx * (n_contexts + 1)
                date_positions.append(base_pos + n_contexts / 2)
                
                for ctx_idx, context in enumerate(context_order):
                    pos = base_pos + ctx_idx
                    tick_positions.append(pos)
                    tick_labels.append(context)
                    
                    date_data = query_data[query_data['datetime_folder'] == date]
                    context_data = date_data[date_data['pf_folder_mapped'] == context]
                    
                    # Track if count text is already added for this context
                    count_text_added = False

                    for model_idx, model in enumerate(sorted(context_data['model_name'].unique())):
                        model_data = context_data[context_data['model_name'] == model]
                        
                        if not model_data.empty:
                            # Scatter the marker
                            # bh_adjusted_p_value
                            # bonferroni_p_value
                            pval = model_data['bh_adjusted_p_value'].iloc[0]
                            effect = model_data['effect_size'].iloc[0]
                            url_count = model_data['Unique_URL_Count'].iloc[0]
                            alpha_val = map_effect_alpha(effect)
                            color_val = get_effect_color(effect)
                            # 점 찍기
                            ax.scatter([pos],
                                    [pval],
                                    marker=markers[model_idx % len(markers)],
                                    color=color_val,
                                    s=400,
                                    alpha=alpha_val,
                                    zorder=3)

                            if pval < 0.05:
                                ax.scatter([pos],
                                        [pval],
                                        marker=markers[model_idx % len(markers)],
                                        color=color_val,
                                        s=400,
                                        alpha=alpha_val,
                                        edgecolor='black',
                                        linewidth=1.5,
                                        zorder=5)

                            # 고유 URL 수 텍스트
                            if not count_text_added:
                                # 모든 URL 수 텍스트를 차트 중간(y=0.5)에 표시
                                ax.text(pos,
                                        0.5,  # 항상 차트 중간에 표시
                                        f'{url_count}',
                                        fontsize=13,
                                        rotation=80,
                                        alpha=0.8,
                                        color='black',
                                        ha='center',
                                        va='center')
                                count_text_added = True
                            
                if date_idx < len(unique_dates) - 1:
                    ax.axvline(x=base_pos + n_contexts + 0.5,
                             color='lightgray',
                             linestyle='-',
                             alpha=0.3,
                             zorder=1)
                
                # Label dates
                ax.text(base_pos + n_contexts / 2, 
                       -0.15, 
                       date.strftime('%m-%d'),
                       ha='center',
                       va='top',
                       transform=ax.get_xaxis_transform(),
                       fontsize=18,
                       fontweight='bold')
            
            ax.set_title(f'{query}', fontsize=18)
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.set_ylim(-0.05, 1.15)
            
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, 
                             rotation=0, 
                             ha='center',
                             fontsize=18)
            
            # ax.set_ylabel('P-value', fontsize=14)
            ## 하이라이트되도록 변경
            ax.axhline(y=0.05, color='blue', linestyle=':', alpha=1, zorder=0)
            
        # fig.suptitle(f'P-value Trends ({search_engine})', fontsize=20, y=1.02)
        plt.tight_layout()
        
        filename = os.path.join(base_folder, f'p_value_trends_{search_engine}.png')
        plt.savefig(filename, dpi=600, bbox_inches='tight')
        plt.close()
        
        print(f"Created visualization for {search_engine}")

def main(df, base_folder='4'):
    # 'political'과 'stance' 컬럼만 포함, model_name 필터 적용
    df = df[df['model_name'].isin(['Political_Score', 'Stance_Score'])]
    df['datetime_folder'] = pd.to_datetime(df['datetime_folder'])
    df = df.sort_values(['query', 'datetime_folder', 'model_name', 'pir_folder'])
    create_grid_plots(df, base_folder)

if __name__ == "__main__":
    # 2024-09
    # 0921_4dim_perspective
    setting_date = '0921-30'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, f'4/tests_{setting_date}.csv')
    df = pd.read_csv(csv_path)
    print(df.head())
    main(df)