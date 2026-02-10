import streamlit as st

def renderizar_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg", width=100)

        if st.session_state.usuario_info.get("is_logged_in", False):
            st.markdown(f"""
            <div class="profile-card">
                <h3>{st.session_state.usuario_info["name"]}</h3>
                <small>{st.session_state.usuario_info["email"]}</small>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.detalhes_usuario:
                st.success("✅ Perfil Carregado")

            if st.button("Sair (Logout)", type="secondary"):
                st.logout()
        else:
            st.warning("Usuário não identificado.")