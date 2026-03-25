import json
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, accuracy_score
from data.nomes_especies import NOMES_COMUNS_ESPECIES

warnings.filterwarnings("ignore", category=UserWarning)

# Sinônimos de ausência → tudo que significa "sem animal"
SINONIMOS_AUSENCIA = {
    "null", "none", "absent", "vazio", "empty", "",
    "nan", "background", "nenhum", "nenhuma", "n/a", "na",
}

# Espécies válidas (normalizadas: sem espaços, lowercase)
ESPECIES_VALIDAS = {
    chave.replace(" ", "").lower()
    for chave in NOMES_COMUNS_ESPECIES.keys()
}


def normalizar_label(texto_bruto: str) -> str:
    # Recebe o nome vindo do dataset ou do modelo e padroniza para um formato rigoroso sem espaços nem maiúsculas.
    # Garante que comparações mínimas não resultem em erros (Ex: 'Sciurus spadiceus.' vira 'sciurusspadiceus').
    if pd.isna(texto_bruto):
        return "background"

    limpo = str(texto_bruto).lower().strip().rstrip(".,;:!?")

    if limpo in SINONIMOS_AUSENCIA:
        return "background"

    return limpo.replace(" ", "").replace("_", "")


def parsear_resposta(resposta_bruta: str) -> str:
    # Tenta decodificar o JSON originário da predição do modelo e extrai a chave do animal.
    # Em seguida, valida se o animal extraído faz parte do inventário oficial de espécies permitidas.
    try:
        dados = resposta_bruta if isinstance(resposta_bruta, dict) else json.loads(resposta_bruta)
        predicao = dados.get("scientific_name") or dados.get("nome_cientifico") or "background"
        label = normalizar_label(str(predicao))

        if label in ESPECIES_VALIDAS:
            return label
        return "erro_ou_desconhecido"
    except Exception:
        return "erro_formatacao"

def preparar_dados_analise(dados_brutos: pd.DataFrame) -> pd.DataFrame:
    # Desestrutura a tabela pareada (duelos A contra B) para um formato longo e "achatado" (1 avaliação por linha).
    # Mantém intencionalmente predições repetidas do mesmo modelo para a mesma imagem, 
    # já que LLMs usando Temperatura > 0.0 podem iterar predições estocásticas em avaliações subsequentes.
    if dados_brutos.empty:
        return pd.DataFrame(columns=["modelo", "imagem", "verdade", "predicao"])

    registros = []
    for _, linha in dados_brutos.iterrows():
        especie_verdadeira = normalizar_label(linha["species"])
        imagem = linha.get("image_id") or linha.get("image_path") or ""

        registros.append({
            "modelo": linha["model_a"],
            "imagem": imagem,
            "verdade": especie_verdadeira,
            "predicao": parsear_resposta(linha["model_response_a"])
        })
        registros.append({
            "modelo": linha["model_b"],
            "imagem": imagem,
            "verdade": especie_verdadeira,
            "predicao": parsear_resposta(linha["model_response_b"])
        })

    df = pd.DataFrame(registros)

    return df



def calcular_metricas_globais(pool_normalizado: pd.DataFrame) -> pd.DataFrame:
    # Calcula métricas globais: Macro F1-Score, Acurácia e Recall Médio usando scikit-learn.
    # Esta função consolida os acertos de forma agrupada por modelo.
    if pool_normalizado.empty:
        return pd.DataFrame()

    lista_ranking = []

    # Itera de forma independente sobre o subset de predições de cada modelo
    for nome_modelo in pool_normalizado["modelo"].unique():
        subconjunto = pool_normalizado[pool_normalizado["modelo"] == nome_modelo]

        # Mapeia dinamicamente apenas as espécies que este modelo realmente avaliou ou tentou prever.
        # Isso impede que o sklearn derrube as notas do modelo usando espécies ausentes no subconjunto.
        categorias_do_modelo = sorted(
            set(subconjunto["verdade"].unique()) | set(subconjunto["predicao"].unique())
        )

        # classification_report gera as métricas detalhadas (F1, Precision, Recall) numa única tacada.
        # labels=categorias_do_modelo restringe o escopo de penalizações às classes que ele de fato viu.
        # zero_division=0 evita warnings do sklearn se a divisão precisar ser resolvida em casos de zero suporte.
        relatorio = classification_report(
            subconjunto["verdade"],
            subconjunto["predicao"],
            labels=categorias_do_modelo,
            output_dict=True,
            zero_division=0
        )

        # O classification_report traz o campo especial "accuracy" no diretório primário do dict.
        # accuracy_score atua apenas como fallback seguro caso a chave do dict falhar.
        acuracia = relatorio.get("accuracy", accuracy_score(subconjunto["verdade"], subconjunto["predicao"]))

        # Armazena e arredonda os dados processados para ranqueamento final
        lista_ranking.append({
            "Modelo":              nome_modelo,
            "Macro F1-Score":      round(relatorio["macro avg"]["f1-score"], 3),
            "Acurácia Global (%)": round(acuracia * 100, 1),
            "Recall Médio":        round(relatorio["macro avg"]["recall"], 3),
            "Amostras":            len(subconjunto)
        })

    # Converte para DataFrame e ordena decrescentemente pelo melhor F1-Score
    # redefinindo o indexador numérico para iniciar visualmente em 1
    tabela = pd.DataFrame(lista_ranking).sort_values(
        "Macro F1-Score", ascending=False
    ).reset_index(drop=True)
    tabela.index += 1
    
    return tabela


def calcular_matriz_confusao(pool_normalizado: pd.DataFrame, modelo_alvo: str):
    # Entrega a Matriz de Confusão 2D avaliando exclusivamente as classes preditas e as classes reais para o modelo.
    # A união dos 2 sets garante que omissões ('background') ou alucinações ("predição" x ausente) entrem na matriz perfeitamente.
    if pool_normalizado.empty:
        return None, []

    subconjunto = pool_normalizado[pool_normalizado["modelo"] == modelo_alvo]
    if subconjunto.empty:
        return None, []

    # União das classes reais e preditas para não omitir categorias como erro_ou_desconhecido
    todas_especies = sorted(
        set(pool_normalizado["verdade"].unique()) | set(pool_normalizado["predicao"].unique())
    )

    matriz = confusion_matrix(
        subconjunto["verdade"],
        subconjunto["predicao"],
        labels=todas_especies
    )

    return matriz, todas_especies


def calcular_metricas_binarias(pool_normalizado: pd.DataFrame, especie_alvo: str) -> pd.DataFrame:
    # Recalcula as estatísticas globais num formato taxonômico binário "One-Vs-Rest" focado estritamente num animal que o avaliador escolha.
    # Revelando assim o raio-x exato de precisão, positivos verdadeiros e falso positivos queletivos daquela classe alvo, contra as outras espécies.
    if pool_normalizado.empty:
        return pd.DataFrame()

    especie_normalizada = normalizar_label(especie_alvo)
    lista_resultados = []

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
            "Modelo":           nome_modelo,
            "Acurácia (%)":     round(acuracia * 100, 1),
            "F1-Score":         round(pontuacao_f1, 3),
            "Recall":           round(revocacao, 3),
            "Precision":        round(precisao, 3),
            "Taxa de Erro (%)": round((1.0 - acuracia) * 100, 1),
            "Verdadeiros Positivos": int(verdadeiros_positivos),
            "Falsos Positivos": int(falsos_positivos),
            "Falsos Negativos": int(falsos_negativos)
        })

    return pd.DataFrame(lista_resultados).sort_values(
        "F1-Score", ascending=False
    ).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
#    RANKING POR VOTAÇÃO HUMANA
#    Sistemas de ranking baseados nos votos dos avaliadores humanos,
#    seguindo a metodologia Chatbot Arena (LMSYS).
# ══════════════════════════════════════════════════════════════════════════════

def calcular_bradley_terry(dados_brutos: pd.DataFrame) -> pd.DataFrame:
    # Modela as vitórias relativas entre 2 modelos assumindo o framework matemático de Bradley-Terry (utilizado no Xadrez ou em Ratings Glicko).
    # Em vez de mle (manual iterativo propenso ao L-BFGS-B min/max throw), usamos um classificador Linear via Regressão Logística L2 no Sklearn,
    # garantindo penalidade em pontuações imensas e convergência exata, transformando duelos em samples de Loss Funciona Binario (-1 e 1).
    if dados_brutos.empty:
        return pd.DataFrame()

    from sklearn.linear_model import LogisticRegression

    lista_modelos = sorted(set(dados_brutos["model_a"].unique()) | set(dados_brutos["model_b"].unique()))
    numero_modelos = len(lista_modelos)
    indice_modelo = {modelo: indice for indice, modelo in enumerate(lista_modelos)}

    X = []
    y = []
    pesos = []

    for _, linha in dados_brutos.iterrows():
        resultado = linha.get("result_code", "")
        if not isinstance(resultado, str) or not resultado:
            continue

        indice_a = indice_modelo[linha["model_a"]]
        indice_b = indice_modelo[linha["model_b"]]

        x_vec = np.zeros(numero_modelos)
        x_vec[indice_a] = 1.0
        x_vec[indice_b] = -1.0

        if resultado == "A>B":
            X.append(x_vec)
            y.append(1)
            pesos.append(1.0)
        elif resultado == "A<B":
            X.append(x_vec)
            y.append(0)
            pesos.append(1.0)
        elif resultado in ["A=B_GOOD", "!A!B"]:
            # Empate técnico: meias vitórias
            X.append(x_vec)
            y.append(1)
            pesos.append(0.5)
            X.append(x_vec)
            y.append(0)
            pesos.append(0.5)

    if not X:
        return pd.DataFrame()

    X = np.array(X)
    y = np.array(y)
    pesos = np.array(pesos)

    # Treina o modelo logístico; a regularização L2 (C=1.0) evita coeficientes 
    # infinitos (erros L-BFGS-B min/max) garantindo que o ranking sempre convirja
    modelo_lr = LogisticRegression(fit_intercept=False, l1_ratio=0, C=1.0)
    modelo_lr.fit(X, y, sample_weight=pesos)

    # Os coeficientes da regressão logística equivalem exatamente às forças do modelo de Bradley-Terry
    pontuacoes = modelo_lr.coef_[0]
    pontuacoes = pontuacoes - np.mean(pontuacoes)

    tabela_bradley_terry = pd.DataFrame({
        "Modelo": lista_modelos,
        "BT Score (Logit)": np.round(pontuacoes, 3)
    })

    tabela_bradley_terry = tabela_bradley_terry.sort_values(
        "BT Score (Logit)", ascending=False
    ).reset_index(drop=True)
    tabela_bradley_terry.index += 1

    return tabela_bradley_terry


def calcular_elo_rating(dados_brutos: pd.DataFrame, fator_k=32) -> pd.DataFrame:
    # Ratings Elo Dinâmicos — Cada modelo ganha e perde pontos com base na expectativa estatística do confronto (como em Campeonatos).
    # O valor padrão k=32 garante flutuação normal da taxa. Caso um competidor (IA inferior) abata um de alta qualificação, o payout é alto.
    if dados_brutos.empty:
        return pd.DataFrame()

    lista_modelos = sorted(set(dados_brutos["model_a"].unique()) | set(dados_brutos["model_b"].unique()))
    pontuacoes = {modelo: 1000.0 for modelo in lista_modelos}

    for _, linha in dados_brutos.iterrows():
        resultado = linha.get("result_code", "")

        if resultado == "A>B":
            resultado_real_a = 1.0
        elif resultado == "A<B":
            resultado_real_a = 0.0
        elif resultado in ["A=B_GOOD", "!A!B"]:
            resultado_real_a = 0.5
        else:
            # Ignora resultados nulos ou strings inválidas
            continue

        rating_modelo_a = pontuacoes[linha["model_a"]]
        rating_modelo_b = pontuacoes[linha["model_b"]]

        resultado_esperado_a = 1 / (1 + 10 ** ((rating_modelo_b - rating_modelo_a) / 400))

        pontuacoes[linha["model_a"]] += fator_k * (resultado_real_a - resultado_esperado_a)
        pontuacoes[linha["model_b"]] += fator_k * ((1 - resultado_real_a) - (1 - resultado_esperado_a))

    lista_elo = [
        {"Modelo": modelo, "Elo Rating": int(round(pontuacoes[modelo]))}
        for modelo in lista_modelos
    ]

    tabela_elo = pd.DataFrame(lista_elo).sort_values(
        "Elo Rating", ascending=False
    ).reset_index(drop=True)
    tabela_elo.index += 1

    return tabela_elo