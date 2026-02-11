import streamlit as st

def renderizar_sidebar():
    with st.sidebar:
        st.markdown("### 🛡️ EcoLLM Arena")

        if st.session_state.usuario_info.get("email"):
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
        
        # === ÚLTIMO DUELO (só aparece após avaliar) ===
        historico = st.session_state.get("historico_duelos", [])
        if historico:
            st.divider()
            st.markdown("### 🔓 Último Duelo")
            d = historico[0]
            st.caption(
                f"**Espécie:** {d['especie']}\n\n"
                f"🅰️ `{d['modelo_a']}`\n\n"
                f"🅱️ `{d['modelo_b']}`"
            )