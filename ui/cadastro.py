import streamlit as st
import time
from data.database import salvar_perfil_novo

def form_cadastro():
    st.info("👋 Olá! Antes de começar, precisamos conhecer seu perfil técnico.")

    with st.form("cadastro_completo"):
        c1, c2 = st.columns(2)
        with c1:
            inst = st.text_input("Instituição (Ex: UFAM)")
            prof = st.text_input("Profissão / Curso")
            idade = st.number_input("Idade", min_value=10, max_value=100, step=1)
        with c2:
            genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro", "Prefiro não dizer"])
            st.markdown("**Experiência Técnica:**")
            area_amb = st.checkbox("Trabalha/Estuda na área ambiental?")
            manejo = st.checkbox("Já fez manejo florestal?")
            monitor = st.checkbox("Já trabalhou com monitoramento de animais?")
            camera = st.checkbox("Já trabalhou com armadilhas fotográficas?")

        if st.form_submit_button("Salvar e Continuar", width='stretch'):
            if inst and prof:
                email = st.session_state.usuario_info.get("email") or ""
                email = email.lower().strip()
                name = st.session_state.usuario_info.get("name") or "Usuário"
                
                if not email or "@" not in email:
                    st.error("Email inválido. Faça login novamente.")
                    st.stop()
                
                dados_usuario = {
                    "email": email,
                    "name": name,
                    "institution": inst,
                    "profession": prof,
                    "age": idade,
                    "gender": genero,
                    "works_environmental_area": area_amb,
                    "has_forest_management_exp": manejo,
                    "has_animal_monitoring_exp": monitor,
                    "has_camera_trap_exp": camera
                }

                if salvar_perfil_novo(dados_usuario):
                    st.session_state.detalhes_usuario = dados_usuario
                    st.success("Cadastro realizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Por favor, preencha Instituição e Profissão.")