import streamlit as st
from html import escape as html_escape

def renderizar_sidebar():
    with st.sidebar:
        st.markdown("### EcoLLM Arena")

        if st.session_state.usuario_info.get("email"):
            nome_seguro = html_escape(str(st.session_state.usuario_info["name"]))
            email_seguro = html_escape(str(st.session_state.usuario_info["email"]))
            st.markdown(f"""
            <div class="profile-card">
                <h3>{nome_seguro}</h3>
                <small>{email_seguro}</small>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.detalhes_usuario:
                st.success("Perfil Carregado")

            if st.button("Sair (Logout)", type="secondary"):
                st.logout()
        else:
            st.warning("Usuário não identificado.")
        
        # Último Duelo
        historico = st.session_state.get("historico_duelos", [])
        if historico:
            st.divider()
            st.markdown("### Último Duelo")
            d = historico[0]
            st.caption(
                f"**Espécie:** {d['especie']}\n\n"
                f"A: `{d['modelo_a']}`\n\n"
                f"B: `{d['modelo_b']}`"
            )