import streamlit as st
import json
import random
import time
from ai.prompt import PROMPT_TEMPLATE
from utils.image import codificar_imagem
from utils.json_utils import decodificar_json
from ai.models import executar_analise
from data.database import salvar_avaliacao
from data.drive import obter_imagem_aleatoria
from config import TEMPERATURA_FIXA
from data.nomes_especies import NOMES_COMUNS_ESPECIES

def render_arena():
    st.caption("Compare modelos e ajude a classificar a melhor IA para biologia.")
    
    with st.expander("Como funciona este duelo? (Clique para ver as instruções)"):
            st.markdown("""
            **Bem-vindo à Arena EcoLLM!**
            Sua participação é essencial para validar modelos de IA no monitoramento da fauna amazônica.

            1. **Sorteio:** Uma imagem de armadilha fotográfica será carregada aleatoriamente.
            2. **Teste Cego:** Dois modelos de IA analisarão a imagem sem acesso ao gabarito.
            3. **Votação:** Você, como especialista humano, avalia qual modelo teve o melhor desempenho.

            **Critério de Avaliação Principal:**
            * A identificação correta da espécie é o fator eliminatório. Um modelo que gera uma descrição detalhada, mas erra a espécie (alucinação), deve ser penalizado.

            **Opções de Voto:**
            * **Vitória (Modelo A ou B):** O modelo acertou a identificação da espécie e o outro errou. Se ambos acertarem, vence aquele que apresentou a melhor justificativa com base na imagem (características visuais, comportamento ou habitat).
            * **Ambos Bons:** Ambos acertaram a espécie de forma exata e forneceram descrições ricas e úteis, não sendo possível distinguir um vencedor.
            * **Ambos Ruins:** Ambos erraram a identificação grosseiramente ou inventaram animais que não estão na imagem. Nesse caso, o sistema pedirá que você descreva brevemente o que realmente há na foto.
            """)

    # Se houve falha, não bloqueamos o botão
    falha_detectada = st.session_state.analise_executada and not (st.session_state.sucesso_modelo_a and st.session_state.sucesso_modelo_b)
    processando_ou_avaliando = st.session_state.duelo_ativo and not st.session_state.avaliacao_enviada and not falha_detectada
    
    if st.button("Sortear Novo Duelo", type="primary", disabled=processando_ou_avaliando):
        st.session_state.duelo_ativo = True
        st.session_state.analise_executada = False
        st.session_state.avaliacao_enviada = False
        st.rerun()
    
    if st.session_state.duelo_ativo and not st.session_state.analise_executada:
        with st.spinner("Carregando duelo..."):
            dados_img = obter_imagem_aleatoria()
            
            if not dados_img:
                st.error("Nenhuma imagem disponível no dataset.")
                st.session_state.duelo_ativo = False
                st.stop()
            
            img, nome_arq, especie, id_arq = dados_img
            st.session_state.imagem = img
            st.session_state.nome_imagem = nome_arq
            st.session_state.pasta_especie = especie
            st.session_state.id_imagem = id_arq
            
            mods = list(st.session_state.modelos_disponiveis.keys())
            if len(mods) < 2:
                st.error("Não há modelos suficientes configurados (mínimo 2).")
                st.session_state.duelo_ativo = False
                st.stop()
            
            st.session_state.modelo_a, st.session_state.modelo_b = random.sample(mods, 2)
            
            print(f"[DUELO] Modelo A: {st.session_state.modelo_a} | Modelo B: {st.session_state.modelo_b}")
            print(f"[DUELO] Espécie: {especie} | Imagem: {nome_arq}")
            
            enc = codificar_imagem(st.session_state.imagem)
            
            # Blind test: não informar espécie
            prompt_blind = PROMPT_TEMPLATE 
            st.session_state.prompt_usado = prompt_blind
            
            sucesso_a, resposta_a, tempo_a = executar_analise(
                st.session_state.modelo_a, 
                prompt_blind, 
                st.session_state.imagem, 
                enc
            )
            
            sucesso_b, resposta_b, tempo_b = executar_analise(
                st.session_state.modelo_b, 
                prompt_blind, 
                st.session_state.imagem, 
                enc
            )
            
            st.session_state.update({
                "resposta_modelo_a": resposta_a, 
                "tempo_modelo_a": tempo_a, 
                "sucesso_modelo_a": sucesso_a,
                "resposta_modelo_b": resposta_b, 
                "tempo_modelo_b": tempo_b, 
                "sucesso_modelo_b": sucesso_b,
                "analise_executada": True
            })
        
        st.rerun()
    
    if st.session_state.analise_executada and st.session_state.imagem:
        sucesso_total = st.session_state.sucesso_modelo_a and st.session_state.sucesso_modelo_b

        if sucesso_total:
            col_img, col_texto = st.columns([0.4, 0.6])

            with col_img:
                st.markdown("#### Imagem da Armadilha")
                
                # Buscar nome comum
                # Buscar nome comum e formatar científico
                especie_raw = st.session_state.pasta_especie
                nome_comum = NOMES_COMUNS_ESPECIES.get(especie_raw, especie_raw)
                cientifico_formatado = especie_raw

                # Tenta recuperar o nome científico formatado (com espaços) se não bater direto
                if especie_raw not in NOMES_COMUNS_ESPECIES:
                    for k, v in NOMES_COMUNS_ESPECIES.items():
                        # Compara ignorando espaços e case
                        if k.replace(" ", "").lower() == especie_raw.replace(" ", "").lower():
                            nome_comum = v
                            cientifico_formatado = k # Usa a chave do dicionário (Ex: "Tupinambis teguixin")
                            break
                
                legenda = f"Científico: {cientifico_formatado}"
                if nome_comum != cientifico_formatado:
                    legenda = f"**{nome_comum}** ({cientifico_formatado})"
                
                st.image(
                    st.session_state.imagem,
                    caption=f"{legenda} | Contexto: Selva Amazônica",
                    width='stretch'
                )

            with col_texto:
                st.markdown("#### Prompt Enviado (Blind Test)")
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
                st.subheader("Modelo A")
                st.caption(f"Tempo: {st.session_state.tempo_modelo_a:.2f}s")
                json_a_ok = decodificar_json(st.session_state.resposta_modelo_a)
            with c2:
                st.subheader("Modelo B")
                st.caption(f"Tempo: {st.session_state.tempo_modelo_b:.2f}s")
                json_b_ok = decodificar_json(st.session_state.resposta_modelo_b)

            if not json_a_ok or not json_b_ok:
                st.warning("Um ou ambos os modelos não geraram JSON válido. Sorteie um novo duelo.")
                st.info(f"Revelação: A = {st.session_state.modelo_a} | B = {st.session_state.modelo_b}")
                return

            if not st.session_state.avaliacao_enviada:
                st.divider()
                st.markdown("### Qual seu veredito?")

                voto = st.radio("Qual modelo descreveu melhor?",
                                [
                                    "Modelo A (Vitória)", 
                                    "Modelo B (Vitória)", 
                                    "Ambos Bons (Excelência)", 
                                    "Ambos Ruins (Falha Mútua)"
                                ],
                                index=None,
                                horizontal=True)

                obs = ""
                if voto == "Ambos Ruins (Falha Mútua)":
                    st.warning("Como os dois modelos falharam na identificação ou na descrição, solicitamos sua anotação manual. Por favor, informe a espécie correta e descreva o registro (consultas a fontes externas para confirmação são permitidas).")
                    
                    especie_real = st.session_state.pasta_especie
                    
                    if especie_real.lower() == "background":
                        nome_comum_real = "BACKGROUND"
                        feedback_quantidade = 0
                    else:
                        nome_comum_real = NOMES_COMUNS_ESPECIES.get(especie_real, especie_real)
                        feedback_quantidade = st.number_input("Número de Indivíduos", min_value=1, value=1, step=1)

                    feedback_desc = st.text_area("Descrição Visual Correta", help="Descreva o animal e a cena como deveria ser.")
                    
                    feedback_dict = {
                        "especie_correta": especie_real,
                        "nome_comum": nome_comum_real,
                        "quantidade": feedback_quantidade,
                        "descricao": feedback_desc
                    }
                    obs = json.dumps(feedback_dict, ensure_ascii=False)
                else:
                    obs = ""

                if st.button("Confirmar Avaliação", type="primary"):
                    if voto == "Ambos Ruins (Falha Mútua)":
                        dados_fb = json.loads(obs)
                        if len(dados_fb["descricao"].strip()) < 5:
                            st.error("Para classificar como 'Ambos Ruins', por favor forneça uma Descrição Visual válida.")
                            st.stop()
                    
                    if voto:
                        mapa_voto = {
                            "Modelo A (Vitória)": "A>B", 
                            "Modelo B (Vitória)": "A<B", 
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
                            "model_response_a": st.session_state.resposta_modelo_a,
                            "model_response_b": st.session_state.resposta_modelo_b,
                            "result_code": codigo_resultado,
                            "text_len_a": len(st.session_state.resposta_modelo_a) if st.session_state.resposta_modelo_a else 0,
                            "text_len_b": len(st.session_state.resposta_modelo_b) if st.session_state.resposta_modelo_b else 0,
                            "time_a": st.session_state.tempo_modelo_a,
                            "time_b": st.session_state.tempo_modelo_b,
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
                                st.success("Avaliação Científica Registrada! Obrigado.")
                                st.info(f"Revelação: A = {st.session_state.modelo_a} | B = {st.session_state.modelo_b}")
                                time.sleep(3)
                                st.rerun()
                            else:
                                st.error("Erro ao salvar avaliação. Tente novamente.")
                        except Exception as e:
                            print(f"[ERRO] Erro ao salvar avaliação (UI): {e}")
                            erro = str(e).lower()
                            if "connection" in erro:
                                st.error("Erro de Conexão: Verifique sua internet.")
                            elif "timeout" in erro:
                                st.error("Erro: O servidor demorou para responder.")
                            else:
                                st.error("Erro na operação. Tente novamente.")

        else:
            st.error("Duelo cancelado: Um ou ambos os modelos falharam na análise.")
            detalhes = []
            if not st.session_state.sucesso_modelo_a: 
                detalhes.append(f"Erro {st.session_state.modelo_a}")
            if not st.session_state.sucesso_modelo_b: 
                detalhes.append(f"Erro {st.session_state.modelo_b}")
            st.text("Modelos com erro:\n" + "\n".join(detalhes))