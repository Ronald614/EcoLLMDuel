import streamlit as st
from config import CSS_STYLES
from utils.session import init
from ui.sidebar import renderizar_sidebar
from ui.cadastro import form_cadastro
from ui.arena import render_arena
from ui.ranking import render_ranking
from data.database import verificar_perfil

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="EcoLLMDuel", page_icon="🤖")

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
                "is_logged_in": True,
                "loaded_from_oauth": True
            }
        else:
            # Mostrar tela de login
            st.title("🔐 Login Necessário")
            st.write("Por favor, faça login com sua conta Google para continuar.")
            if st.button("Fazer Login com Google", type="primary"):
                try:
                    st.login("google")
                except Exception as e:
                    st.error(f"⚠️ Erro na autenticação: {str(e)[:200]}")
            st.stop()
    
    # === SIDEBAR ===
    renderizar_sidebar()

    # === VERIFICAÇÃO DE PERFIL ===
    if not st.session_state.detalhes_usuario:
        email = st.session_state.usuario_info.get("email")
        if not email:
            st.title("🔐 Login Necessário")
            st.write("Sessão expirada. Por favor, faça login novamente.")
            if st.button("Fazer Login com Google", type="primary", key="login_retry"):
                try:
                    st.login("google")
                except Exception as e:
                    st.error(f"⚠️ Erro na autenticação: {str(e)[:200]}")
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
    st.title("🛡️ EcoLLM Arena")

    tab_arena, tab_rank = st.tabs(["⚔️ Arena de Duelo", "🏆 Leaderboard (Rank)"])

    with tab_arena:
        render_arena()

    with tab_rank:
        render_ranking()

if __name__ == "__main__":
    main()