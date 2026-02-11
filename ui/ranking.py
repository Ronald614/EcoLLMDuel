import streamlit as st
import pandas as pd
from data.database import carregar_dados_duelos
from data.ranking import calcular_elo, calcular_bradley_terry, calcular_acuracia
from utils.json_utils import extrair_json

def render_global_stats(df_duelos):
    st.header("🏆 Classificação Global")
    if not df_duelos.empty:
        total_batalhas = len(df_duelos)
        # Total de modelos únicos considerando ambas as colunas
        total_modelos = len(set(df_duelos['model_a'].unique()) | set(df_duelos['model_b'].unique()))

        m1, m2 = st.columns(2)
        m1.metric("Total de Batalhas", total_batalhas)
        m2.metric("Modelos Avaliados", total_modelos)
        st.divider()
    else:
        st.info("Nenhum duelo realizado ainda.")

def render_elo(df_duelos):
    st.subheader("📈 Elo Rating System")
    if not df_duelos.empty:
        df_elo = calcular_elo(df_duelos)
        st.dataframe(df_elo, width='stretch', column_config={"Elo Rating": st.column_config.NumberColumn(format="%.0f")})
    else:
        st.info("Sem dados para Elo.")

def render_bt(df_duelos):
    st.subheader("📊 Bradley-Terry Model")
    if not df_duelos.empty:
        df_bt = calcular_bradley_terry(df_duelos)
        st.dataframe(
            df_bt, width='stretch',
            column_config={
                "BT Score": st.column_config.ProgressColumn(
                    format="%.2f",
                    min_value=0,
                    max_value=max(df_bt['BT Score']) if not df_bt.empty else 1000
                )
            }
        )
    else:
        st.info("Sem dados para Bradley-Terry.")

def render_acc(df_duelos):
    st.subheader("🎯 Taxa de Acerto (Binária)")
    st.write("Considera 'Acerto' se o modelo identificou corretamente a espécie (match parcial) ou se identificou corretamente 'Nenhum' animal para imagens de background.")
    if not df_duelos.empty:
        df_acc = calcular_acuracia(df_duelos)
        st.dataframe(
            df_acc, width='stretch',
            column_config={
                "Acurácia": st.column_config.ProgressColumn(
                    format="%.1f%%",
                    min_value=0,
                    max_value=1
                )
            }
        )
    else:
        st.info("Sem dados para Acurácia.")