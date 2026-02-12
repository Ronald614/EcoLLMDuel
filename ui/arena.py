import streamlit as st
import random
import time
from ai.prompt import PROMPT_TEMPLATE
from utils.image import codificar_imagem
from utils.json_utils import decodificar_json
from ai.models import executar_analise
from data.database import salvar_avaliacao
from data.drive import obter_imagem_aleatoria
from config import TEMPERATURA_FIXA
from data.species_names import SPECIES_COMMON_NAMES

def render_arena():
    st.caption("Compare modelos e ajude a classificar a melhor IA para biologia.")

    processando = st.session_state.duelo_ativo and not st.session_state.analise_executada
    
    if st.button("🔄 Sortear Novo Duelo", type="primary", disabled=processando):
        st.session_state.duelo_ativo = True
        st.session_state.analise_executada = False
        st.session_state.avaliacao_enviada = False
        st.rerun()
    
    if st.session_state.duelo_ativo and not st.session_state.analise_executada:
        with st.spinner("Carregando duelo..."):
            dados_img = obter_imagem_aleatoria()
            
            if not dados_img:
                st.error("❌ Nenhuma imagem disponível no dataset.")
                st.session_state.duelo_ativo = False
                st.stop()
            
            img, nome_arq, especie, id_arq = dados_img
            st.session_state.imagem = img
            st.session_state.nome_imagem = nome_arq
            st.session_state.pasta_especie = especie
            st.session_state.id_imagem = id_arq
            
            mods = list(st.session_state.modelos_disponiveis.keys())
            if len(mods) < 2:
                st.error("❌ Não há modelos suficientes configurados (mínimo 2).")
                st.session_state.duelo_ativo = False
                st.stop()
            
            st.session_state.modelo_a, st.session_state.modelo_b = random.sample(mods, 2)
            
            print(f"🎲 [DUELO] Modelo A: {st.session_state.modelo_a} | Modelo B: {st.session_state.modelo_b}")
            print(f"📸 [DUELO] Espécie: {especie} | Imagem: {nome_arq}")
            
            enc = codificar_imagem(st.session_state.imagem)
            
            # Blind test: não informar espécie
            prompt_blind = PROMPT_TEMPLATE 
            st.session_state.prompt_usado = prompt_blind
            
            sa, ra, ta = executar_analise(
                st.session_state.modelo_a, 
                prompt_blind, 
                st.session_state.imagem, 
                enc
            )
            time.sleep(1)
            
            
            sb, rb, tb = executar_analise(
                st.session_state.modelo_b, 
                prompt_blind, 
                st.session_state.imagem, 
                enc
            )
            
            st.session_state.update({
                "resp_a": ra, 
                "time_a": ta, 
                "suc_a": sa,
                "resp_b": rb, 
                "time_b": tb, 
                "suc_b": sb,
                "analise_executada": True
            })
        
        st.rerun()
    
    if st.session_state.analise_executada and st.session_state.imagem:
        sucesso_total = st.session_state.suc_a and st.session_state.suc_b

        if sucesso_total:
            col_img, col_texto = st.columns([0.4, 0.6])

            with col_img:
                st.markdown("#### 📸 Imagem da Armadilha")
                st.image(
                    st.session_state.imagem,
                    caption=f"Espécie: {st.session_state.pasta_especie} | Contexto: Selva Amazônica",
                    width='stretch'
                )

            with col_texto:
                st.markdown("#### 📝 Prompt Enviado (Blind Test)")
                st.text_area(
                    label="Prompt",
                    value=st.session_state.get("prompt_usado", PROMPT_TEMPLATE),
                    height=300,
                    disabled=True,
                    label_visibility="collapsed"
                )

            st.divider()

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🅰️ Modelo A")
                st.caption(f"Tempo: {st.session_state.time_a:.2f}s")
                json_a_ok = decodificar_json(st.session_state.resp_a)
            with c2:
                st.subheader("🅱️ Modelo B")
                st.caption(f"Tempo: {st.session_state.time_b:.2f}s")
                json_b_ok = decodificar_json(st.session_state.resp_b)

            if not json_a_ok or not json_b_ok:
                st.warning("⚠️ Um ou ambos os modelos não geraram JSON válido. Sorteie um novo duelo.")
                st.info(f"🔓 **Revelação:** A = {st.session_state.modelo_a} | B = {st.session_state.modelo_b}")
                return

            if not st.session_state.avaliacao_enviada:
                st.divider()
                st.markdown("### 👨‍⚖️ Qual seu veredito?")

                voto = st.radio("Qual modelo descreveu melhor?",
                                [
                                    "Modelo A (Vitória)", 
                                    "Modelo B (Vitória)", 
                                    "Empate (Neutro)", 
                                    "Ambos Bons (Excelência)", 
                                    "Ambos Ruins (Falha Mútua)"
                                ],
                                index=None,
                                horizontal=True)

                obs = ""
                if voto == "Ambos Ruins (Falha Mútua)":
                    st.warning("Se ambos os modelos não mencionaram corretamente a espécie e não descreveram corretamente o habitat forneça para nós uma descrição melhor, preencha os campos com base nas informações da imagem")
                    
                    especie_real = st.session_state.pasta_especie
                    
                    if especie_real.lower() == "background":
                        st.info("⚠️ **Esta foto não contém nenhum animal !**")
                        nome_comum_real = "N/A" # Conteúdo interno
                    else:
                        nome_comum_real = SPECIES_COMMON_NAMES.get(especie_real, "Não listado")
                        st.info(f"🧬 **Espécie Identificada:** {especie_real} ({nome_comum_real})")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                         feedback_quantidade = st.number_input("Número de Indivíduos", min_value=1, value=1, step=1)
                    with c2:
                        feedback_habitat = st.text_input("Habitat / Contexto")

                    feedback_desc = st.text_area("Descrição Visual Correta", help="Descreva o animal e a cena como deveria ser.")
                    
                    import json
                    feedback_dict = {
                        "especie_correta": especie_real,
                        "nome_comum": nome_comum_real,
                        "quantidade": feedback_quantidade,
                        "descricao": feedback_desc,
                        "habitat": feedback_habitat
                    }
                    obs = json.dumps(feedback_dict, ensure_ascii=False)
                else:
                    obs = ""

                if st.button("✅ Confirmar Avaliação", type="primary"):
                    if voto == "Ambos Ruins (Falha Mútua)":
                        dados_fb = json.loads(obs)
                        if len(dados_fb["descricao"].strip()) < 5:
                            st.error("⚠️ Para classificar como 'Ambos Ruins', por favor forneça uma Descrição Visual válida.")
                            st.stop()
                    
                    if voto:
                        mapa_voto = {
                            "Modelo A (Vitória)": "A>B", 
                            "Modelo B (Vitória)": "A<B", 
                            "Empate (Neutro)": "A=B", 
                            "Ambos Bons (Excelência)": "A=B_GOOD",
                            "Ambos Ruins (Falha Mútua)": "!A!B"
                        }
                        
                        codigo_resultado = mapa_voto[voto]

                        email = st.session_state.usuario_info.get("email", "")
                        if email:
                            email = email.lower().strip()
                        
                        if not email or "@" not in email:
                            st.error("Email inválido. Faça login novamente.")
                            st.stop()
                        
                        dados_salvar = {
                            "evaluator_email": email,
                            "image_name": st.session_state.nome_imagem,
                            "image_id": st.session_state.id_imagem,
                            "species_folder": st.session_state.pasta_especie,
                            "model_a": st.session_state.modelo_a,
                            "model_b": st.session_state.modelo_b,
                            "model_response_a": st.session_state.resp_a,
                            "model_response_b": st.session_state.resp_b,
                            "result_code": codigo_resultado,
                            "text_len_a": len(st.session_state.resp_a) if st.session_state.resp_a else 0,
                            "text_len_b": len(st.session_state.resp_b) if st.session_state.resp_b else 0,
                            "time_a": st.session_state.time_a,
                            "time_b": st.session_state.time_b,
                            "comments": obs,
                            "prompt": st.session_state.get("prompt_usado", PROMPT_TEMPLATE),
                            "temperature": TEMPERATURA_FIXA
                        }
                        
                        try:
                            if salvar_avaliacao(dados_salvar):
                                st.session_state.avaliacao_enviada = True
                                st.session_state.historico_duelos = [{
                                    "modelo_a": st.session_state.modelo_a,
                                    "modelo_b": st.session_state.modelo_b,
                                    "especie": st.session_state.pasta_especie
                                }]
                                st.success("🎉 Avaliação Científica Registrada! Obrigado.")
                                st.info(f"🔓 **Revelação:** A = {st.session_state.modelo_a} | B = {st.session_state.modelo_b}")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao salvar avaliação. Tente novamente.")
                        except Exception as e:
                            st.error(f"❌ Erro na operação: {str(e)[:100]}")

        else:
            st.error("⚠️ Duelo cancelado: Um ou ambos os modelos falharam na análise.")
            detalhes = []
            if not st.session_state.suc_a: 
                detalhes.append(f"❌ {st.session_state.modelo_a}")
            if not st.session_state.suc_b: 
                detalhes.append(f"❌ {st.session_state.modelo_b}")
            st.text("Modelos com erro:\n" + "\n".join(detalhes))