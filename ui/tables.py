import streamlit as st
from data.ranking import (
    calcular_elo_rating, 
    calcular_bradley_terry, 
    calcular_acuracia,
    preparar_dados_analise,
    calcular_metricas_globais,
    calcular_metricas_binarias,
    calcular_matriz_confusao
)
import plotly.express as px
from data.species_names import SPECIES_COMMON_NAMES


def _obter_nome_exibicao(especie_raw: str) -> str:
    """Retorna 'Nome Comum (Nome Científico)' para exibição."""
    nome_comum = especie_raw
    cientifico_formatado = especie_raw

    for chave, valor in SPECIES_COMMON_NAMES.items():
        if chave.replace(" ", "").lower() == especie_raw.replace(" ", "").lower():
            nome_comum = valor
            cientifico_formatado = chave
            break

    if nome_comum != cientifico_formatado:
        return f"{nome_comum} ({cientifico_formatado})"
    return especie_raw


def render_global_stats(df_duelos):
    st.header("🏆 Classificação Global")
    if not df_duelos.empty:
        total_batalhas = len(df_duelos)
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
        df_flat = preparar_dados_analise(df_duelos)
        df_acc = calcular_acuracia(df_flat)
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


def render_species_analysis(df_duelos):
    st.divider()
    st.subheader("Análise Binária por Espécie")
    st.caption("Selecione uma espécie para ver detalhes de performance 'Um-contra-Todos'.")

    if df_duelos.empty:
        st.info("Sem dados para análise.")
        return

    df_flat = preparar_dados_analise(df_duelos)
    todas_especies = sorted(df_flat['verdade'].unique())
    
    # Criar mapa para exibição no Selectbox
    opcoes_especies = [_obter_nome_exibicao(sp) for sp in todas_especies]
    mapa_reverso = {_obter_nome_exibicao(sp): sp for sp in todas_especies}

    selecao = st.selectbox("Escolha a Espécie:", options=opcoes_especies)

    if selecao:
        especie_real = mapa_reverso[selecao]
        df_especie = calcular_metricas_binarias(df_flat, especie_real)

        coluna_tabela, coluna_grafico = st.columns([0.65, 0.35])

        with coluna_tabela:
            st.markdown("##### Métricas Detalhadas")
            st.dataframe(
                df_especie,
                width='stretch',
                column_config={
                    "F1-Score": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                    "Taxa de Erro": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                    "Precision": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                    "Recall": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
                    "Verdadeiros Positivos": st.column_config.NumberColumn(format="%d"),
                    "Falsos Positivos": st.column_config.NumberColumn(format="%d"),
                    "Falsos Negativos": st.column_config.NumberColumn(format="%d")
                }
            )

        with coluna_grafico:
            if not df_especie.empty:
                st.markdown("##### Diagnóstico de Erros")
                # Gráfico de Barras Empilhadas para TP, FP, FN
                df_long = df_especie.melt(
                    id_vars=["Modelo"], 
                    value_vars=["Verdadeiros Positivos", "Falsos Positivos", "Falsos Negativos"],
                    var_name="Tipo",
                    value_name="Quantidade"
                )
                
                color_map = {
                    "Verdadeiros Positivos": "#2ecc71", # Verde
                    "Falsos Positivos": "#e74c3c",      # Vermelho
                    "Falsos Negativos": "#f1c40f"       # Amarelo
                }

                fig = px.bar(
                    df_long,
                    x="Quantidade",
                    y="Modelo",
                    color="Tipo",
                    orientation='h',
                    color_discrete_map=color_map,
                    text_auto=True
                )
                fig.update_layout(
                    showlegend=True, 
                    margin=dict(l=0, r=0, t=0, b=0), 
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, key=f"grafico_stacked_{especie_real}")
                
                st.caption("Verde: Acertos | Vermelho: Alucinações | Amarelo: Omissões")


def render_macro_f1(df_duelos):
    st.subheader("Ranking Global (Macro F1-Score)")
    st.markdown("""
    **Por que Macro F1?**  
    O dataset é desbalanceado (muitas onças/vazio, poucos tatus). A Acurácia simples mascara erros nas classes raras.
    O **Macro F1** calcula a média harmônica de precisão e recall para *cada espécie* e tira a média, dando peso igual a todas as classes.
    """)

    if not df_duelos.empty:
        df_flat = preparar_dados_analise(df_duelos)
        df_macro = calcular_metricas_globais(df_flat)

        st.dataframe(
            df_macro, width='stretch',
            column_config={
                "Macro F1-Score": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
                "Acurácia Global": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)
            }
        )
    else:
        st.info("Sem dados para Macro F1.")


def render_matriz_confusao_global(df_duelos):
    st.divider()
    st.subheader("Diagnóstico Visual de Erros (Matriz de Confusão)")
    st.caption("Visualize onde cada modelo está errando. Eixo X: Predição, Eixo Y: Verdade.")

    if df_duelos.empty:
        return

    df_flat = preparar_dados_analise(df_duelos)
    modelos = sorted(df_flat["modelo"].unique())
    
    col_sel, col_viz = st.columns([0.3, 0.7])
    
    with col_sel:
        modelo_selecionado = st.selectbox("Selecione o Modelo:", modelos)
    
    if modelo_selecionado:
        matriz, labels = calcular_matriz_confusao(df_flat, modelo_selecionado)
        
        if matriz is not None:
            # Labels formatados para o gráfico
            labels_display = [_obter_nome_exibicao(l) for l in labels]
            
            fig = px.imshow(
                matriz,
                labels=dict(x="Predição", y="Verdade (Real)", color="Quantidade"),
                x=labels_display,
                y=labels_display,
                text_auto=True,
                color_continuous_scale="Blues",
                aspect="auto"
            )
            fig.update_layout(height=500)
            
            with col_viz:
                st.plotly_chart(fig, key=f"heatmap_{modelo_selecionado}")