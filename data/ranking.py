import json
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.optimize import minimize
from sklearn.metrics import classification_report
from utils.json_utils import extrair_json

# Ignorar avisos de divisão por zero em classes que o modelo nunca previu (F1=0 é o correto)
warnings.filterwarnings("ignore", category=UserWarning)


ABSENT_SYNONYMS = {"null", "none", "absent", "vazio", "empty", "", "nan", "background", "nenhum"}

def normalizar_label(raw: str) -> str:
    limpo = str(raw).lower().strip()
    return "background" if limpo in ABSENT_SYNONYMS else limpo


def parsear_resposta(raw_response: str) -> str:
    try:
        # Se já vier como dict (alguns fluxos do Streamlit), usa direto
        if isinstance(raw_response, dict):
            data = raw_response
        else:
            # Tenta decodificar string JSON
            data = json.loads(raw_response)
        
        # Busca flexível pelos campos do Schema
        pred = data.get("scientific_name") or data.get("nome_cientifico") or "background"
        return normalizar_label(str(pred))
    except Exception:
        return "erro_formatacao"


def construir_pool(df_raw: pd.DataFrame) -> pd.DataFrame:
    records = []
    if df_raw.empty:
        return pd.DataFrame(columns=["modelo", "verdade", "predicao"])

    for _, row in df_raw.iterrows():
        target = normalizar_label(row["species"])
        
        # Processa Modelo A
        records.append({
            "modelo": row["model_a"],
            "verdade": target,
            "predicao": parsear_resposta(row["model_response_a"])
        })
        
        # Processa Modelo B
        records.append({
            "modelo": row["model_b"],
            "verdade": target,
            "predicao": parsear_resposta(row["model_response_b"])
        })

    return pd.DataFrame(records)


def calcular_acuracia(df):
    if df.empty: return pd.DataFrame()
    
    # Coletar modelos
    todos_modelos = list(set(df['model_a'].unique()) | set(df['model_b'].unique()))
    stats = {m: {'total': 0, 'acertos': 0} for m in todos_modelos}
    
    for _, row in df.iterrows():
        especie_real = str(row['species']).strip().lower()
        if especie_real in ["empty", "vazio", "nenhum", "none", "null"]:
             especie_real = "background"
        
        # Processar Modelo A
        try:
            json_a = extrair_json(row['model_response_a'])
            if json_a:
                nome_cientifico_a = str(json_a.get("nome_cientifico", "")).strip().lower()
                deteccao_a = str(json_a.get("deteccao", "")).strip().lower()
                
                # Caso Background/Vazio
                if especie_real == "background":
                     if deteccao_a == "nenhuma" or nome_cientifico_a in ["nenhum", "none", "", "background"]:
                         stats[row['model_a']]['acertos'] += 1
                
                # Caso Espécie Normal
                else:
                    # Fuzzy match simples
                    if especie_real in nome_cientifico_a or nome_cientifico_a in especie_real:
                        stats[row['model_a']]['acertos'] += 1
            
            stats[row['model_a']]['total'] += 1
        except:
            pass 

        # Processar Modelo B
        try:
            json_b = extrair_json(row['model_response_b'])
            if json_b:
                nome_cientifico_b = str(json_b.get("nome_cientifico", "")).strip().lower()
                deteccao_b = str(json_b.get("deteccao", "")).strip().lower()
                
                if especie_real == "background":
                     if deteccao_b == "nenhuma" or nome_cientifico_b in ["nenhum", "none", "", "background"]:
                         stats[row['model_b']]['acertos'] += 1
                else:
                    if especie_real in nome_cientifico_b or nome_cientifico_b in especie_real:
                        stats[row['model_b']]['acertos'] += 1
            
            stats[row['model_b']]['total'] += 1
        except:
            pass

    # Criar DataFrame
    dados_acc = []
    for m, s in stats.items():
        if s['total'] > 0:
            acc = s['acertos'] / s['total']
        else:
            acc = 0.0
        dados_acc.append({"Modelo": m, "Acurácia": acc, "Total Amostras": s['total']})
    
    df_acc = pd.DataFrame(dados_acc).sort_values(by="Acurácia", ascending=False).reset_index(drop=True)
    df_acc.index += 1
    return df_acc




def calcular_ranking_macro_f1(df_pool: pd.DataFrame) -> pd.DataFrame:
    if df_pool.empty:
        return pd.DataFrame()

    ranking = []
    # Definir todas as espécies possíveis para garantir que classes zeradas apareçam
    todas_especies = sorted(df_pool["verdade"].unique())

    for mod in df_pool["modelo"].unique():
        subset = df_pool[df_pool["modelo"] == mod]
        
        # classification_report com output_dict=True gera todas as métricas
        report = classification_report(
            subset["verdade"],
            subset["predicao"],
            labels=todas_especies, # Força inclusão de todas as classes
            output_dict=True,
            zero_division=0
        )
        
        ranking.append({
            "Modelo":          mod,
            "Macro F1-Score":  round(report["macro avg"]["f1-score"], 4),
            "Acurácia Global": round(report.get("accuracy", 0.0), 4),
            "Recall Médio":    round(report["macro avg"]["recall"], 4),
            "Amostras":        len(subset)
        })

    return pd.DataFrame(ranking).sort_values("Macro F1-Score", ascending=False).reset_index(drop=True)




def analise_por_especie(df_pool: pd.DataFrame, especie_alvo: str) -> pd.DataFrame:
    target = normalizar_label(especie_alvo)
    resultados = []
    
    if df_pool.empty:
        return pd.DataFrame()

    for mod in df_pool["modelo"].unique():
        subset = df_pool[df_pool["modelo"] == mod]
        
        # Cria vetores binários: 1 se for a espécie alvo, 0 se não for
        y_true = (subset["verdade"] == target).astype(int)
        y_pred = (subset["predicao"] == target).astype(int)
        
        # Matriz de confusão binária
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        
        # Métricas
        suporte = tp + fn
        total = tp + fp + fn + tn
        
        # Evita divisão por zero
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy  = (tp + tn) / total if total > 0 else 0.0
        
        resultados.append({
            "Modelo":       mod,
            "Taxa de Erro": round(1.0 - accuracy, 4), # O inverso da acurácia
            "F1-Score":     round(f1, 4),
            "Recall":       round(recall, 4),
            "Precision":    round(precision, 4),
            "TP": int(tp), "FP": int(fp), "FN": int(fn) # Útil para debug
        })
        
    return pd.DataFrame(resultados).sort_values("F1-Score", ascending=False).reset_index(drop=True)




def calcular_bradley_terry(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw.empty: return pd.DataFrame()

    modelos = sorted(list(set(df_raw["model_a"].unique()) | set(df_raw["model_b"].unique())))
    n_models = len(modelos)
    idx_map = {m: i for i, m in enumerate(modelos)}
    
    # Matriz de vitórias (Wins)
    W = np.zeros((n_models, n_models))
    
    for _, row in df_raw.iterrows():
        # Verifica quem acertou
        truth = normalizar_label(row["species"])
        p_a = parsear_resposta(row["model_response_a"])
        p_b = parsear_resposta(row["model_response_b"])
        
        ok_a = (p_a == truth)
        ok_b = (p_b == truth)
        
        # Se ambos erraram, ignora (duelo nulo)
        if not ok_a and not ok_b:
            continue
            
        i, j = idx_map[row["model_a"]], idx_map[row["model_b"]]
        
        if ok_a and not ok_b:
            W[i][j] += 1
        elif ok_b and not ok_a:
            W[j][i] += 1
        else: # Empate (ambos acertaram)
            W[i][j] += 0.5
            W[j][i] += 0.5

    # Função de verossimilhança negativa
    def neg_log_likelihood(params):
        # params são log-probabilidades (logits)
        # exp(params) garante positividade
        pi = np.exp(params)
        ll = 0
        epsilon = 1e-9 # Evita log(0)
        
        for i in range(n_models):
            for j in range(n_models):
                if i != j and W[i][j] > 0:
                    prob_i_vence_j = pi[i] / (pi[i] + pi[j] + epsilon)
                    ll += W[i][j] * np.log(prob_i_vence_j + epsilon)
        return -ll

    # Otimização
    x0 = np.zeros(n_models)
    res = minimize(neg_log_likelihood, x0, method='L-BFGS-B')
    
    # Centralizar scores (média 0)
    scores = res.x - np.mean(res.x)
    
    # Escalar para facilitar leitura (tipo Elo, base 1000 + desvio)
    # Ou deixar puro Logit. Vamos usar Logit puro arredondado.
    return pd.DataFrame({
        "Modelo": modelos,
        "BT Score (Logit)": np.round(scores, 3)
    }).sort_values("BT Score (Logit)", ascending=False).reset_index(drop=True)


def calcular_elo_rating(df_raw: pd.DataFrame, k_factor=32) -> pd.DataFrame:
    if df_raw.empty: return pd.DataFrame()

    modelos = sorted(list(set(df_raw["model_a"].unique()) | set(df_raw["model_b"].unique())))
    ratings = {m: 1000.0 for m in modelos}
    
    for _, row in df_raw.iterrows():
        truth = normalizar_label(row["species"])
        p_a = parsear_resposta(row["model_response_a"])
        p_b = parsear_resposta(row["model_response_b"])
        
        ok_a = (p_a == truth)
        ok_b = (p_b == truth)
        
        if not ok_a and not ok_b: continue # Ignora se ambos erram
        
        # Define resultado S_a
        if ok_a and not ok_b: s_a = 1.0
        elif ok_b and not ok_a: s_a = 0.0
        else: s_a = 0.5
        
        ra = ratings[row["model_a"]]
        rb = ratings[row["model_b"]]
        
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        
        ratings[row["model_a"]] += k_factor * (s_a - ea)
        ratings[row["model_b"]] += k_factor * ((1 - s_a) - (1 - ea))
        
    return pd.DataFrame([
        {"Modelo": m, "Elo Rating": round(r, 0)} for m, r in ratings.items()
    ]).sort_values("Elo Rating", ascending=False).reset_index(drop=True)