import pandas as pd
import numpy as np

def calcular_elo(df, k_factor=32):
    if df.empty: return pd.DataFrame()
    
    # Coletar TODOS os modelos antes de filtrar
    todos_modelos = set(df['model_a'].unique()) | set(df['model_b'].unique())
    ratings = {model: 1000.0 for model in todos_modelos}

    # Ignorar !A!B (Ambos Ruins) apenas para o cálculo
    df_valido = df[df['result_code'] != '!A!B']

    for _, row in df_valido.iterrows():
        r_a = ratings[row['model_a']]
        r_b = ratings[row['model_b']]
        
        code = row['result_code']
        if code == 'A>B': s_a = 1.0
        elif code == 'A<B': s_a = 0.0
        else: s_a = 0.5

        e_a = 1 / (1 + 10 ** ((r_b - r_a) / 400))
        ratings[row['model_a']] = r_a + k_factor * (s_a - e_a)
        ratings[row['model_b']] = r_b + k_factor * ((1 - s_a) - (1 - e_a))

    rank_df = pd.DataFrame(list(ratings.items()), columns=['Modelo', 'Elo Rating'])
    rank_df = rank_df.sort_values(by='Elo Rating', ascending=False).reset_index(drop=True)
    rank_df.index += 1
    return rank_df

def calcular_bradley_terry(df, iterações=100):
    if df.empty: return pd.DataFrame()
    
    # Coletar TODOS os modelos antes de filtrar
    todos_modelos = list(set(df['model_a'].unique()) | set(df['model_b'].unique()))

    # Filtrar !A!B apenas para o cálculo
    df_valido = df[df['result_code'] != '!A!B']

    models = todos_modelos
    n_models = len(models)
    model_to_idx = {m: i for i, m in enumerate(models)}
    wins = np.zeros((n_models, n_models))
    matches = np.zeros((n_models, n_models))

    for _, row in df_valido.iterrows():
        idx_a = model_to_idx[row['model_a']]
        idx_b = model_to_idx[row['model_b']]
        matches[idx_a][idx_b] += 1
        matches[idx_b][idx_a] += 1
        
        code = row['result_code']
        if code == 'A>B': wins[idx_a][idx_b] += 1
        elif code == 'A<B': wins[idx_b][idx_a] += 1
        else:
            wins[idx_a][idx_b] += 0.5
            wins[idx_b][idx_a] += 0.5

    p = np.ones(n_models) / n_models
    for _ in range(iterações):
        p_new = np.zeros(n_models)
        total_wins = np.sum(wins, axis=1)
        for i in range(n_models):
            soma_denominador = 0
            for j in range(n_models):
                if i != j and matches[i][j] > 0:
                    soma_denominador += matches[i][j] / (p[i] + p[j])
            if soma_denominador > 0: p_new[i] = total_wins[i] / soma_denominador
            else: p_new[i] = p[i]
        p_new /= np.sum(p_new)
        p = p_new

    scores = p * 10000
    rank_df = pd.DataFrame({'Modelo': models, 'BT Score': scores})
    rank_df = rank_df.sort_values(by='BT Score', ascending=False).reset_index(drop=True)
    rank_df.index += 1
    return rank_df