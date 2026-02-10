import streamlit as st

def renderizar_sidebar():
    with st.sidebar:
        st.markdown("### 🛡️ EcoLLM Arena")

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
        
        # === HISTÓRICO DE DUELOS ===
        historico = st.session_state.get("historico_duelos", [])
        if historico:
            st.divider()
            st.markdown("### 📜 Últimos Duelos")
            for i, d in enumerate(historico):
                status_a = "✅" if d["suc_a"] else "❌"
                status_b = "✅" if d["suc_b"] else "❌"
                st.caption(
                    f"**#{i+1}** {d['especie']}\n\n"
                    f"{status_a} `{d['modelo_a']}`\n\n"
                    f"{status_b} `{d['modelo_b']}`"
                )