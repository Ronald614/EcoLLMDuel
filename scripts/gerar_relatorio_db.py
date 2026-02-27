#!/usr/bin/env python3
# Relatório rápido: participação dos modelos e avaliadores.
# Uso: streamlit run scripts/gerar_relatorio_db.py

import sys
from pathlib import Path

# Adiciona raiz do projeto ao path para importar módulos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from data.ranking import preparar_dados_analise
from data.nomes_especies import obter_nome_exibicao

st.set_page_config(page_title="Relatório EcoLLMDuel", layout="wide")
st.title("Relatório de Participação - EcoLLMDuel")


def carregar_avaliacoes():
    conn = st.connection("evaluations_db", type="sql", url=st.secrets["DATABASE_URL"])
    query = "SELECT model_a, model_b, evaluator_email, result_code, species, model_response_a, model_response_b FROM evaluations"
    return conn.query(query, ttl=0, show_spinner=False)


df = carregar_avaliacoes()

if df.empty:
    st.warning("Nenhuma avaliação encontrada.")
    st.stop()

# --- Números gerais ---
total_duelos = len(df)
total_avaliadores = df["evaluator_email"].nunique()

contagem_a = df["model_a"].value_counts()
contagem_b = df["model_b"].value_counts()
participacao = contagem_a.add(contagem_b, fill_value=0).astype(int).sort_values(ascending=False)
total_modelos = len(participacao)

c1, c2, c3 = st.columns(3)
c1.metric("Total de Duelos", total_duelos)
c2.metric("Avaliadores Únicos", total_avaliadores)
c3.metric("Modelos Utilizados", total_modelos)

st.divider()

# --- Quantas vezes cada modelo rodou ---
st.subheader("Quantas vezes cada modelo participou de um duelo")
df_part = participacao.reset_index()
df_part.columns = ["Modelo", "Participações"]

fig = px.bar(
    df_part.sort_values("Participações"),
    x="Participações", y="Modelo",
    orientation="h",
    text_auto=True,
    color="Participações",
    color_continuous_scale="Blues"
)
fig.update_layout(showlegend=False, height=max(350, len(df_part) * 40), margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig, width='stretch')

st.divider()

# --- Duelos por avaliador ---
st.subheader("Quantos duelos cada avaliador realizou")
duelos_por_avaliador = df["evaluator_email"].value_counts().reset_index()
duelos_por_avaliador.columns = ["Avaliador", "Duelos"]

fig2 = px.bar(
    duelos_por_avaliador.sort_values("Duelos"),
    x="Duelos", y="Avaliador",
    orientation="h",
    text_auto=True,
    color="Duelos",
    color_continuous_scale="Greens"
)
fig2.update_layout(showlegend=False, height=max(300, len(duelos_por_avaliador) * 40), margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig2, width='stretch')

st.divider()

# --- Perfil de resultados por modelo (detecção de anomalias) ---
st.subheader("Perfil de Resultados por Modelo")
st.write("Análise da distribuição de resultados para cada IA. Alta proporção de 'Ambos Ruins' ou 'Derrota' pode indicar falhas sistemáticas.")

# Usa os mesmos dados já carregados
df_full = df

mapa_nomes = {
    "A>B": "Vitória",
    "A<B": "Derrota",
    "A=B": "Empate",
    "A=B_GOOD": "Ambos Bons",
    "!A!B": "Ambos Ruins"
}
mapa_inverso = {
    "A>B": "Derrota",
    "A<B": "Vitória",
    "A=B": "Empate",
    "A=B_GOOD": "Ambos Bons",
    "!A!B": "Ambos Ruins"
}

registros = []
for _, linha in df_full.iterrows():
    registros.append({"Modelo": linha["model_a"], "Resultado": mapa_nomes.get(linha["result_code"], linha["result_code"])})
    registros.append({"Modelo": linha["model_b"], "Resultado": mapa_inverso.get(linha["result_code"], linha["result_code"])})

df_perfil = pd.DataFrame(registros)
df_contagem = df_perfil.groupby(["Modelo", "Resultado"]).size().reset_index(name="Quantidade")

cores = {
    "Vitória": "#2ecc71",
    "Derrota": "#e74c3c",
    "Empate": "#f1c40f",
    "Ambos Bons": "#3498db",
    "Ambos Ruins": "#95a5a6"
}

fig3 = px.bar(
    df_contagem,
    x="Quantidade", y="Modelo",
    color="Resultado",
    orientation="h",
    text_auto=True,
    color_discrete_map=cores,
    barmode="stack"
)
fig3.update_layout(
    height=max(350, len(df_contagem["Modelo"].unique()) * 45),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig3, width='stretch')

st.divider()

# --- Acertos por espécie por modelo ---
st.subheader("Acertos por Espécie")
st.write("Proporção de acertos individuais validada contra o label verdadeiro de cada imagem.")

df_flat = preparar_dados_analise(df)
df_flat["acertou"] = df_flat["verdade"] == df_flat["predicao"]

# Formatar nomes das espécies usando a função centralizada
df_flat["especie_nome"] = df_flat["verdade"].apply(obter_nome_exibicao)

# Tabela: modelo x espécie -> acertos / total
resumo = df_flat.groupby(["modelo", "especie_nome"]).agg(
    total=("acertou", "size"),
    acertos=("acertou", "sum")
).reset_index()
resumo["acertos"] = resumo["acertos"].astype(int)
resumo["texto"] = resumo.apply(lambda r: f"{r['acertos']}/{r['total']}", axis=1)

fig4 = px.bar(
    resumo,
    x="acertos", y="modelo",
    color="especie_nome",
    orientation="h",
    text="texto",
    barmode="group",
    labels={"acertos": "Acertos", "modelo": "Modelo", "especie_nome": "Espécie"}
)
fig4.update_layout(
    height=max(400, len(resumo["modelo"].unique()) * 60),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig4, width='stretch')

# Tabela resumo com taxa
st.subheader("Tabela de Acertos Detalhada")
tabela_acertos = resumo.pivot_table(index="modelo", columns="especie_nome", values="texto", aggfunc="first").fillna("-")
st.dataframe(tabela_acertos, width='stretch')
