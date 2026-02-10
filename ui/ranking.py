import streamlit as st
from data.database import carregar_dados_duelos
from data.ranking import calcular_elo, calcular_bradley_terry

def render_ranking():
    st.header("🏆 Classificação Global")
    st.markdown("Ranking gerado com base em todas as avaliações salvas no banco de dados.")

    if st.button("🔄 Atualizar Ranking"):
        st.rerun()

    df_duelos = carregar_dados_duelos()

    if not df_duelos.empty:
        total_batalhas = len(df_duelos)
        total_modelos = len(set(df_duelos['model_a'].unique()) | set(df_duelos['model_b'].unique()))

        m1, m2 = st.columns(2)
        m1.metric("Total de Batalhas", total_batalhas)
        m2.metric("Modelos Avaliados", total_modelos)

        st.divider()

        st.subheader("📈 Elo Rating System")
        df_elo = calcular_elo(df_duelos)
        st.dataframe(df_elo, width='stretch', column_config={"Elo Rating": st.column_config.NumberColumn(format="%.0f")})

        st.divider()

        st.subheader("📊 Bradley-Terry Model")
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
        st.info("Nenhum duelo realizado ainda.")