import json
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

warnings.filterwarnings("ignore", category=UserWarning)


SINONIMOS_AUSENCIA = {"null", "none", "absent", "vazio", "empty", "", "nan", "background", "nenhum"}

def normalizar_label(texto_bruto: str) -> str:
    # Ex: "Sciurus spadiceus" -> "sciurusspadiceus"
    if pd.isna(texto_bruto): return "background"

    limpo = str(texto_bruto).lower().strip()

    if limpo in SINONIMOS_AUSENCIA:
        return "background"

    limpo = limpo.replace(" ", "").replace("_", "")

    return limpo


def parsear_resposta(resposta_bruta: str) -> str:
    """Extrai o nome científico da resposta JSON do modelo."""
    try:
        if isinstance(resposta_bruta, dict):
            dados = resposta_bruta
        else:
            dados = json.loads(resposta_bruta)
        
        predicao = dados.get("scientific_name") or dados.get("nome_cientifico") or "background"
        return normalizar_label(str(predicao))
    except Exception:
        return "erro_formatacao"


def preparar_dados_analise(dados_brutos: pd.DataFrame) -> pd.DataFrame:
    """Transforma duelos pareados em formato flat (um registro por modelo por imagem)."""
    registros = []
    if dados_brutos.empty:
        return pd.DataFrame(columns=["modelo", "verdade", "predicao"])

    for _, linha in dados_brutos.iterrows():
        especie_verdadeira = normalizar_label(linha["species"])
        
        registros.append({
            "modelo": linha["model_a"],
            "verdade": especie_verdadeira,
            "predicao": parsear_resposta(linha["model_response_a"])
        })
        registros.append({
            "modelo": linha["model_b"],
            "verdade": especie_verdadeira,
            "predicao": parsear_resposta(linha["model_response_b"])
        })

    return pd.DataFrame(registros)


def calcular_acuracia(pool_normalizado: pd.DataFrame) -> pd.DataFrame:
    """Acurácia por match exato, usando o pool normalizado."""
    if pool_normalizado.empty:
        return pd.DataFrame()

    lista_acuracia = []
    for nome_modelo in pool_normalizado["modelo"].unique():
        subconjunto = pool_normalizado[pool_normalizado["modelo"] == nome_modelo]

        lista_acuracia.append({
            "Modelo": nome_modelo,
            #Calcular com o sklearn
            "Acurácia": accuracy_score(subconjunto["verdade"], subconjunto["predicao"]),
            "Total Amostras": len(subconjunto)
        })

    tabela_acuracia = pd.DataFrame(lista_acuracia).sort_values(
        by="Acurácia", ascending=False
    ).reset_index(drop=True)
    tabela_acuracia.index += 1
    return tabela_acuracia


def calcular_metricas_globais(pool_normalizado: pd.DataFrame) -> pd.DataFrame:
    """Macro F1-Score via sklearn, forçando inclusão de todas as classes."""
    if pool_normalizado.empty:
        return pd.DataFrame()

    lista_ranking = []
    todas_especies = sorted(pool_normalizado["verdade"].unique())

    for nome_modelo in pool_normalizado["modelo"].unique():
        subconjunto = pool_normalizado[pool_normalizado["modelo"] == nome_modelo]
        
        relatorio = classification_report(
            subconjunto["verdade"],
            subconjunto["predicao"],
            labels=todas_especies,
            output_dict=True,
            zero_division=0
        )
        
        lista_ranking.append({
            "Modelo":          nome_modelo,
            "Macro F1-Score":  round(relatorio["macro avg"]["f1-score"], 4),
            "Acurácia Global": round(relatorio.get("accuracy", 0.0), 4),
            "Recall Médio":    round(relatorio["macro avg"]["recall"], 4),
            "Amostras":        len(subconjunto)
        })

    return pd.DataFrame(lista_ranking).sort_values("Macro F1-Score", ascending=False).reset_index(drop=True)


def calcular_matriz_confusao(pool_normalizado: pd.DataFrame, modelo_alvo: str):
    """Retorna (matriz_confusao, labels) para um modelo específico."""
    if pool_normalizado.empty:
        return None, []

    subconjunto = pool_normalizado[pool_normalizado["modelo"] == modelo_alvo]
    if subconjunto.empty:
        return None, []
    
    todas_especies = sorted(pool_normalizado["verdade"].unique())
    
    matriz = confusion_matrix(
        subconjunto["verdade"],
        subconjunto["predicao"],
        labels=todas_especies
    )
    
    return matriz, todas_especies


def calcular_metricas_binarias(pool_normalizado: pd.DataFrame, especie_alvo: str) -> pd.DataFrame:
    """Métricas binárias (one-vs-rest) para uma espécie específica."""
    especie_normalizada = normalizar_label(especie_alvo)
    lista_resultados = []
    
    if pool_normalizado.empty:
        return pd.DataFrame()

    for nome_modelo in pool_normalizado["modelo"].unique():
        subconjunto = pool_normalizado[pool_normalizado["modelo"] == nome_modelo]
        
        rotulo_verdadeiro = (subconjunto["verdade"] == especie_normalizada).astype(int)
        rotulo_predito    = (subconjunto["predicao"] == especie_normalizada).astype(int)
        
        verdadeiros_negativos, falsos_positivos, falsos_negativos, verdadeiros_positivos = confusion_matrix(
            rotulo_verdadeiro, rotulo_predito, labels=[0, 1]
        ).ravel()
        
        precisao, revocacao, pontuacao_f1, _ = precision_recall_fscore_support(
            rotulo_verdadeiro, rotulo_predito, average="binary", zero_division=0
        )
        
        acuracia = accuracy_score(rotulo_verdadeiro, rotulo_predito)
        
        lista_resultados.append({
            "Modelo":       nome_modelo,
            "Taxa de Erro": round(1.0 - acuracia, 4),
            "F1-Score":     round(pontuacao_f1, 4),
            "Recall":       round(revocacao, 4),
            "Precision":    round(precisao, 4),
            "Verdadeiros Positivos": int(verdadeiros_positivos),
            "Falsos Positivos": int(falsos_positivos),
            "Falsos Negativos": int(falsos_negativos)
        })
        
    return pd.DataFrame(lista_resultados).sort_values("F1-Score", ascending=False).reset_index(drop=True)


def calcular_bradley_terry(dados_brutos: pd.DataFrame) -> pd.DataFrame:
    """Bradley-Terry (1952) — P(i vence j) = força_i / (força_i + força_j), estimado por MLE."""
    if dados_brutos.empty:
        return pd.DataFrame()

    lista_modelos = sorted(set(dados_brutos["model_a"].unique()) | set(dados_brutos["model_b"].unique()))
    numero_modelos = len(lista_modelos)
    indice_modelo = {modelo: indice for indice, modelo in enumerate(lista_modelos)}
    
    # vitorias[i][j] = vezes que modelo i venceu modelo j
    vitorias = np.zeros((numero_modelos, numero_modelos))
    
    for _, linha in dados_brutos.iterrows():
        especie_verdadeira = normalizar_label(linha["species"])
        predicao_modelo_a = parsear_resposta(linha["model_response_a"])
        predicao_modelo_b = parsear_resposta(linha["model_response_b"])
        
        acertou_modelo_a = (predicao_modelo_a == especie_verdadeira)
        acertou_modelo_b = (predicao_modelo_b == especie_verdadeira)
        
        if not acertou_modelo_a and not acertou_modelo_b:
            continue
            
        indice_a = indice_modelo[linha["model_a"]]
        indice_b = indice_modelo[linha["model_b"]]
        
        if acertou_modelo_a and not acertou_modelo_b:
            vitorias[indice_a][indice_b] += 1
        elif acertou_modelo_b and not acertou_modelo_a:
            vitorias[indice_b][indice_a] += 1
        else:
            vitorias[indice_a][indice_b] += 0.5
            vitorias[indice_b][indice_a] += 0.5

    EPSILON = 1e-9

    def log_verossimilhanca_negativa(parametros):
        forca = np.exp(parametros)
        verossimilhanca = 0
        
        for indice_i in range(numero_modelos):
            for indice_j in range(numero_modelos):
                if indice_i != indice_j and vitorias[indice_i][indice_j] > 0:
                    probabilidade_i_vence_j = forca[indice_i] / (forca[indice_i] + forca[indice_j])
                    verossimilhanca += vitorias[indice_i][indice_j] * np.log(probabilidade_i_vence_j + EPSILON)
        return -verossimilhanca

    ponto_inicial = np.zeros(numero_modelos)
    resultado_otimizacao = minimize(log_verossimilhanca_negativa, ponto_inicial, method='L-BFGS-B')
    
    pontuacoes = resultado_otimizacao.x - np.mean(resultado_otimizacao.x)
    
    tabela_bradley_terry = pd.DataFrame({
        "Modelo": lista_modelos,
        "BT Score (Logit)": np.round(pontuacoes, 3)
    })

    tabela_bradley_terry = tabela_bradley_terry.sort_values(
        "BT Score (Logit)", ascending=False
    ).reset_index(drop=True)

    return tabela_bradley_terry


def _calcular_elo_uma_vez(dados_brutos: pd.DataFrame, fator_ajuste: float) -> dict:
    """Uma rodada de Elo sobre os duelos na ordem dada."""
    lista_modelos = sorted(set(dados_brutos["model_a"].unique()) | set(dados_brutos["model_b"].unique()))
    pontuacoes = {modelo: 1000.0 for modelo in lista_modelos}
    
    for _, linha in dados_brutos.iterrows():
        especie_verdadeira = normalizar_label(linha["species"])
        predicao_modelo_a = parsear_resposta(linha["model_response_a"])
        predicao_modelo_b = parsear_resposta(linha["model_response_b"])
        
        acertou_modelo_a = (predicao_modelo_a == especie_verdadeira)
        acertou_modelo_b = (predicao_modelo_b == especie_verdadeira)
        
        if not acertou_modelo_a and not acertou_modelo_b:
            continue
        
        if acertou_modelo_a and not acertou_modelo_b:
            resultado_real_a = 1.0
        elif acertou_modelo_b and not acertou_modelo_a:
            resultado_real_a = 0.0
        else:
            resultado_real_a = 0.5
        
        rating_modelo_a = pontuacoes[linha["model_a"]]
        rating_modelo_b = pontuacoes[linha["model_b"]]
        
        resultado_esperado_a = 1 / (1 + 10 ** ((rating_modelo_b - rating_modelo_a) / 400))
        
        pontuacoes[linha["model_a"]] += fator_ajuste * (resultado_real_a - resultado_esperado_a)
        pontuacoes[linha["model_b"]] += fator_ajuste * ((1 - resultado_real_a) - (1 - resultado_esperado_a))
    
    return pontuacoes


def calcular_elo_rating(dados_brutos: pd.DataFrame, k_factor=32, n_bootstrap=100) -> pd.DataFrame:
    """Elo com bootstrap — embaralha a ordem N vezes e tira a média (Zheng et al., 2023)."""
    if dados_brutos.empty:
        return pd.DataFrame()

    lista_modelos = sorted(set(dados_brutos["model_a"].unique()) | set(dados_brutos["model_b"].unique()))
    historico_ratings = {modelo: [] for modelo in lista_modelos}
    
    gerador_aleatorio = np.random.default_rng(seed=42)

    for _ in range(n_bootstrap):
        duelos_embaralhados = dados_brutos.sample(
            frac=1,
            random_state=gerador_aleatorio.integers(0, 2**31)
        ).reset_index(drop=True)
        
        ratings_rodada = _calcular_elo_uma_vez(duelos_embaralhados, k_factor)
        
        for modelo in lista_modelos:
            historico_ratings[modelo].append(ratings_rodada[modelo])

    lista_elo = []
    for modelo in lista_modelos:
        media_rating = np.mean(historico_ratings[modelo])
        lista_elo.append({
            "Modelo": modelo,
            "Elo Rating": round(media_rating, 0)
        })

    tabela_elo = pd.DataFrame(lista_elo).sort_values(
        "Elo Rating", ascending=False
    ).reset_index(drop=True)

    return tabela_elo