import streamlit as st
from config import CSS_STYLES
from utils.session import init
from ui.sidebar import renderizar_sidebar
from ui.cadastro import form_cadastro
from ui.arena import render_arena
from ui.tables import (
    render_global_stats, 
    render_elo, 
    render_bt, 
    render_acc,
    render_macro_f1,
    render_species_analysis,
    render_matriz_confusao_global
)
from data.database import verificar_perfil, carregar_dados_duelos

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="EcoLLMDuel", page_icon=None)

# --- CSS ---
st.markdown(CSS_STYLES, unsafe_allow_html=True)

def main():
    init()
    
    # === AUTENTICAÇÃO ===
    if not st.session_state.usuario_info.get("loaded_from_oauth"):
        usuario_logado = False
        
        try:
            usuario_logado = st.user.is_logged_in
        except (AttributeError, Exception):
            pass
        
        if usuario_logado:
            st.session_state.usuario_info = {
                "name": st.user.name,
                "email": st.user.email,
                "loaded_from_oauth": True
            }
        else:
            # Mostrar tela de login
            st.title("Login Necessário")
            st.write("Por favor, faça login com sua conta Google para continuar.")
            if st.button("Fazer Login com Google", type="primary"):
                try:
                    st.login("google")
                except Exception as e:
                    print(f"[ERRO AUTH] {e}")
                    st.error("Falha na autenticação. Tente novamente.")
            st.stop()
    
    # === SIDEBAR ===
    renderizar_sidebar()

    # === VERIFICACAO DE PERFIL ===
    if not st.session_state.detalhes_usuario:
        email = st.session_state.usuario_info.get("email")
        if not email:
            st.title("Login Necessário")
            st.write("Sessão expirada. Por favor, faça login novamente.")
            if st.button("Fazer Login com Google", type="primary", key="login_retry"):
                try:
                    st.login("google")
                except Exception as e:
                    print(f"[ERRO AUTH] {e}")
                    st.error("Falha na autenticação. Tente novamente.")
            st.stop()
        
        with st.spinner("Verificando cadastro..."):
            perfil_existente = verificar_perfil(email)

        if perfil_existente:
            st.session_state.detalhes_usuario = perfil_existente
            st.rerun()
        else:
            st.title("Completar Perfil")
            form_cadastro()
            st.stop()

    # === APP PRINCIPAL ===
    # === CARREGAR DADOS GERAIS ===
    # Carregamos aqui para passar para os rankings sem recarregar várias vezes
    df_duelos = carregar_dados_duelos()


    st.title("EcoLLM Arena")

    tab_arena, tab_elo, tab_bt, tab_binario, tab_geral = st.tabs([
        "Arena de Duelo", 
        "Elo Rating", 
        "Bradley-Terry", 
        "Métricas por Espécies (Binário)",
        "Métricas no Geral (por Classes)"
    ])

    with tab_arena:
        render_arena()

    with tab_elo:
        render_global_stats(df_duelos)
        render_elo(df_duelos)

    with tab_bt:
        render_global_stats(df_duelos)
        render_bt(df_duelos)

    with tab_binario:
        render_global_stats(df_duelos)
        render_acc(df_duelos)
        render_species_analysis(df_duelos)

    with tab_geral:
        render_global_stats(df_duelos)
        render_macro_f1(df_duelos)
        render_matriz_confusao_global(df_duelos)

if __name__ == "__main__":
    main()