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
from data.nomes_especies import NOMES_COMUNS_ESPECIES


def _obter_nome_exibicao(especie_raw: str) -> str:
    """Retorna 'Nome Comum (Nome Científico)' para exibição."""
    nome_comum = especie_raw
    cientifico_formatado = especie_raw

    for chave, valor in NOMES_COMUNS_ESPECIES.items():
        if chave.replace(" ", "").lower() == especie_raw.replace(" ", "").lower():
            nome_comum = valor
            cientifico_formatado = chave
            break

    if nome_comum != cientifico_formatado:
        return f"{nome_comum} ({cientifico_formatado})"
    return especie_raw


def render_global_stats(df_duelos):
    st.header("Visão Geral dos Duelos")
    st.write("Resumo de quantas avaliações já foram realizadas e quantos modelos de IA estão competindo.")
    if not df_duelos.empty:
        total_batalhas = len(df_duelos)
        total_modelos = len(set(df_duelos['model_a'].unique()) | set(df_duelos['model_b'].unique()))

        m1, m2 = st.columns(2)
        m1.metric("Total de Batalhas Avaliadas", total_batalhas)
        m2.metric("IAs Competidoras", total_modelos)
        st.divider()
    else:
        st.info("Ainda não temos dados o suficiente. Participe dos duelos para gerar relatórios!")


def render_elo(df_duelos):
    st.subheader("Sistema de Pontuação (Elo Rating)")
    st.write("Funciona como o ranking do xadrez: a IA ganha pontos ao vencer e perde ao ser derrotada. Vencer uma IA mais forte vale mais pontos.")
    if not df_duelos.empty:
        df_elo = calcular_elo_rating(df_duelos)
        st.dataframe(df_elo, width='stretch', column_config={"Elo Rating": st.column_config.NumberColumn(format="%.0f")})
    else:
        st.info("Sem dados para Elo.")


def render_bt(df_duelos):
    st.subheader("Chances de Vitória (Modelo Bradley-Terry)")
    st.write("A barra indica a força estimada de cada modelo. Quanto mais preenchida, maior a chance dessa IA vencer qualquer confronto.")
    if not df_duelos.empty:
        df_bt = calcular_bradley_terry(df_duelos)

        bt_min = float(df_bt['BT Score (Logit)'].min()) if not df_bt.empty else 0
        bt_max = float(df_bt['BT Score (Logit)'].max()) if not df_bt.empty else 1
        if bt_min >= bt_max:
            bt_min = bt_min - 1
            bt_max = bt_max + 1

        st.dataframe(
            df_bt, width='stretch',
            column_config={
                "BT Score (Logit)": st.column_config.ProgressColumn(
                    format="%.2f",
                    min_value=bt_min,
                    max_value=bt_max
                )
            }
        )
    else:
        st.info("Sem dados para Bradley-Terry.")


def render_acc(df_duelos):
    st.subheader("Taxa de Acerto Simples")
    st.write("Avalia cada IA individualmente. Conta como 'Acerto' quando o modelo identificou o animal correto ou acertou ao dizer que não havia animal na foto.")
    if not df_duelos.empty:
        df_flat = preparar_dados_analise(df_duelos)
        df_acc = calcular_acuracia(df_flat)
        st.dataframe(
            df_acc, width='stretch',
            column_config={
                "Acurácia": st.column_config.ProgressColumn(
                    format="%.4f",
                    min_value=0,
                    max_value=1
                )
            }
        )
    else:
        st.info("Sem dados para Acurácia.")


def render_species_analysis(df_duelos):
    st.divider()
    st.subheader("Análise por Espécie")
    st.write("Selecione um animal abaixo para ver o desempenho de cada IA ao identificá-lo.")

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
                    "F1-Score": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=1),
                    "Taxa de Erro": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=1),
                    "Precision": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=1),
                    "Recall": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=1),
                    "Verdadeiros Positivos": st.column_config.NumberColumn(format="%d"),
                    "Falsos Positivos": st.column_config.NumberColumn(format="%d"),
                    "Falsos Negativos": st.column_config.NumberColumn(format="%d")
                }
            )

        with coluna_grafico:
            if not df_especie.empty:
                st.markdown("##### Diagnóstico de Erros")
                st.write("Veja quantas vezes cada IA acertou, inventou ou deixou de identificar esta espécie:")
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
                
                st.caption("Verde = Acertou | Vermelho = Alucinou (disse que era este animal, mas não era) | Amarelo = Omitiu (o animal estava na foto, mas a IA não o reconheceu)")


def render_macro_f1(df_duelos):
    st.subheader("Ranking de Precisão Justa (Macro F1-Score)")
    st.markdown("""
    Algumas espécies aparecem com muito mais frequência do que outras no dataset. Uma IA poderia inflar sua pontuação acertando apenas os animais comuns e errando os raros.  
    A **Precisão Justa** corrige isso: ela dá peso igual a todas as espécies, penalizando modelos que falham com animais raros. O primeiro lugar aqui é o modelo mais equilibrado.
    """)

    if not df_duelos.empty:
        df_flat = preparar_dados_analise(df_duelos)
        df_macro = calcular_metricas_globais(df_flat)

        st.dataframe(
            df_macro, width='stretch',
            column_config={
                "Macro F1-Score": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=1),
                "Acurácia Global": st.column_config.ProgressColumn(format="%.4f", min_value=0, max_value=1)
            }
        )
    else:
        st.info("Sem dados para Macro F1.")


def render_matriz_confusao_global(df_duelos):
    st.divider()
    st.subheader("Mapa de Confusões da IA")
    st.write("Selecione um modelo abaixo. A diagonal mostra os acertos (quando a IA identificou o animal correto). Quadrados azul-escuro fora da diagonal indicam confusões recorrentes entre duas espécies.")

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