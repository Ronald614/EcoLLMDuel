import streamlit as st
import pandas as pd
from data.database import carregar_dados_duelos
from data.ranking import (
    calcular_elo_rating, 
    calcular_bradley_terry, 
    calcular_acuracia,
    construir_pool,
    calcular_ranking_macro_f1,
    analise_por_especie
)
import plotly.express as px
from utils.json_utils import extrair_json
from data.species_names import SPECIES_COMMON_NAMES

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
        df_elo = calcular_elo_rating(df_duelos)
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
                "BT Score (Logit)": st.column_config.ProgressColumn(
                    format="%.2f",
                    min_value=0,
                    max_value=max(df_bt['BT Score (Logit)']) if not df_bt.empty else 1000
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

def render_macro_f1(df_duelos):
    st.subheader("📊 Relatório Técnico (Macro F1-Score)")
    st.markdown("""
    **Por que Macro F1?**  
    O dataset é desbalanceado (muitas onças/vazio, poucos tatus). A Acurácia simples mascara erros nas classes raras.
    O **Macro F1** calcula a média harmônica de precisão e recall para *cada espécie* e tira a média, dando peso igual a todas as classes.
    """)
    
    if not df_duelos.empty:
        # Preprocessar para formato flat
        df_flat = construir_pool(df_duelos)
        
        # Calcular Ranking
        df_macro = calcular_ranking_macro_f1(df_flat)
        
        st.dataframe(
            df_macro, width='stretch',
            column_config={
                "Macro F1-Score": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
                "Acurácia Global": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)
            }
        )
    else:
        st.info("Sem dados para Macro F1.")

def render_species_analysis(df_duelos):
    st.divider()
    st.subheader("🔍 Análise Granular por Espécie")
    
    if df_duelos.empty:
        st.info("Sem dados para análise.")
        return

    df_flat = construir_pool(df_duelos)
    
    # Seletor com Nome Comum
    todas_especies = sorted(df_flat['verdade'].unique())
    
    # Criar mapa para exibição (Nome Comum | Científico)
    display_map = {}
    for sp in todas_especies:
        # Busca insensível a maiúsculas/minúsculas e espaços
        nome_comum = sp # Default
        cientifico_formatado = sp # Default se não achar
        
        for k, v in SPECIES_COMMON_NAMES.items():
            if k.replace(" ", "").lower() == sp.replace(" ", "").lower():
                nome_comum = v
                cientifico_formatado = k # Usa a chave do dicionário como nome científico oficial
                break
        
        display_map[f"{nome_comum} ({cientifico_formatado})"] = sp

    selected_display = st.selectbox("Selecione a Espécie:", list(display_map.keys()))
    
    if selected_display:
        selected_species = display_map[selected_display]
        df_spp = analise_por_especie(df_flat, selected_species)
        
        c1, c2 = st.columns([0.6, 0.4])
        
        with c1:
            st.markdown(f"**Tabela de Performance: {selected_species}**")
            st.dataframe(
            df_spp, 
            width='stretch',
            column_config={
                "F1-Score": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                "Taxa de Erro": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1, help="1 - Acurácia desta classe"),
                "Precision": st.column_config.NumberColumn(format="%.2f"),
                "Recall": st.column_config.NumberColumn(format="%.2f")
            }
        )
            
        with c2:
            st.markdown(f"**Comparativo Visual (F1)**")
            fig = px.bar(
                df_spp, 
                x='Modelo', 
                y='F1-Score', 
                color='Modelo',
                text_auto='.2%'
            )
            fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=300)
            st.plotly_chart(fig, width='stretch')