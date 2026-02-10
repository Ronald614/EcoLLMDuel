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

def render_arena():
    """
    Arena de Duelo - padrão reativo Streamlit.
    
    Fluxo:
    1. Desencadeador: Usuário clica em "Sortear Novo Duelo"
    2. Lógica: Se duelo_ativo e não analise_executada, rodar análise
    3. Renderização: Mostrar resultados baseado em estado
    """
    st.caption("Compare modelos e ajude a classificar a melhor IA para biologia.")

    # ===== CAMADA 1: DESENCADEADORES =====
    # Travar botão enquanto análise está rodando
    processando = st.session_state.duelo_ativo and not st.session_state.analise_executada
    
    if st.button("🔄 Sortear Novo Duelo", type="primary", disabled=processando):
        st.session_state.duelo_ativo = True
        st.session_state.analise_executada = False
        st.session_state.avaliacao_enviada = False
        st.rerun()
    
    # ===== CAMADA 2: LÓGICA (Estado → Cálculos) =====
    # Se duelo foi acionado mas análise não foi feita, executar
    if st.session_state.duelo_ativo and not st.session_state.analise_executada:
        with st.spinner("Carregando duelo..."):
            # 2.1: Carregar imagem aleatória
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
            
            # 2.2: Selecionar 2 modelos aleatoriamente
            mods = list(st.session_state.modelos_disponiveis.keys())
            if len(mods) < 2:
                st.error("❌ Não há modelos suficientes configurados (mínimo 2).")
                st.session_state.duelo_ativo = False
                st.stop()
            
            st.session_state.modelo_a, st.session_state.modelo_b = random.sample(mods, 2)
            
            # LOG: Modelos sorteados
            print(f"🎲 [DUELO] Modelo A: {st.session_state.modelo_a} | Modelo B: {st.session_state.modelo_b}")
            print(f"📸 [DUELO] Espécie: {especie} | Imagem: {nome_arq}")
            
            # 2.3: Codificar imagem
            enc = codificar_imagem(st.session_state.imagem)
            
            # 2.4: Montar prompt com nome da espécie
            prompt_com_especie = PROMPT_TEMPLATE + f"\nConsiderando a espécie '{especie}' pertencente à imagem, utilize essa informação como contexto adicional para sua análise."
            st.session_state.prompt_usado = prompt_com_especie
            
            # 2.5: Executar análise nos dois modelos
            sa, ra, ta = executar_analise(
                st.session_state.modelo_a, 
                prompt_com_especie, 
                st.session_state.imagem, 
                enc
            )
            time.sleep(1)  # Pequeno delay entre chamadas
            
            sb, rb, tb = executar_analise(
                st.session_state.modelo_b, 
                prompt_com_especie, 
                st.session_state.imagem, 
                enc
            )
            
            # 2.5: Atualizar estado com resultados
            st.session_state.update({
                "resp_a": ra, 
                "time_a": ta, 
                "suc_a": sa,
                "resp_b": rb, 
                "time_b": tb, 
                "suc_b": sb,
                "analise_executada": True
            })
        
        st.rerun()  # ← ÚNICO rerun autorizado na lógica
    
    # ===== CAMADA 3: RENDERIZAÇÃO (Estado → UI) =====
    # Mostrar resultados APENAS se análise foi executada
    if st.session_state.analise_executada and st.session_state.imagem:
        sucesso_total = st.session_state.suc_a and st.session_state.suc_b

        if sucesso_total:
            col_img, col_texto = st.columns([0.4, 0.6])

            with col_img:
                st.markdown("#### 📸 Imagem da Armadilha")
                st.image(
                    st.session_state.imagem,
                    caption=f"Espécie: {st.session_state.pasta_especie}",
                    width='stretch'
                )

            with col_texto:
                st.markdown("#### 📝 Prompt Enviado")
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

            # Se algum modelo não gerou JSON válido, não abrir formulário
            if not json_a_ok or not json_b_ok:
                st.warning("⚠️ Um ou ambos os modelos não geraram JSON válido. Sorteie um novo duelo.")
                st.info(f"🔓 **Revelação:** A = {st.session_state.modelo_a} | B = {st.session_state.modelo_b}")
                return

            if not st.session_state.avaliacao_enviada:
                st.divider()
                st.markdown("### 👨‍⚖️ Qual seu veredito?")

                # Lógica de Votação (5 Opções Científicas)
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
                # Campo condicional: Obrigatório se "Ambos Ruins"
                if voto == "Ambos Ruins (Falha Mútua)":
                    st.markdown("**⚠️ AVISO DE QUALIDADE:** Para 'Ambos Ruins', você **DEVE** fornecer a justificativa ou a identificação correta. Isso criará um dataset de correção (Ground Truth).")
                    obs = st.text_area("Justificativa / Espécie Correta (Obrigatório)*")
                else:
                    obs = st.text_area("Comentários (Opcional)")

                if st.button("✅ Confirmar Avaliação", type="primary"):
                    # Validação de campo obrigatório (Regra 3)
                    if voto == "Ambos Ruins (Falha Mútua)" and len(obs.strip()) < 10:
                        st.error("⚠️ Para classificar como 'Ambos Ruins', a justificativa é OBRIGATÓRIA e deve ter conteúdo relevante.")
                        st.stop()
                    
                    elif voto:
                        # Mapeamento Científico (Regra 4)
                        mapa_voto = {
                            "Modelo A (Vitória)": "A>B", 
                            "Modelo B (Vitória)": "A<B", 
                            "Empate (Neutro)": "A=B", 
                            "Ambos Bons (Excelência)": "A=B_GOOD",
                            "Ambos Ruins (Falha Mútua)": "!A!B"
                        }
                        
                        codigo_resultado = mapa_voto[voto]

                        # Preparar dados para salvar
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
                        
                        # Tentar salvar no banco
                        try:
                            if salvar_avaliacao(dados_salvar):
                                st.session_state.avaliacao_enviada = True
                                # Salvar no histórico APÓS o voto (teste cego preservado)
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
            # Mostrar erro se um dos modelos falhou
            st.error("⚠️ Duelo cancelado: Um ou ambos os modelos falharam na análise.")
            detalhes = []
            if not st.session_state.suc_a: 
                detalhes.append(f"❌ {st.session_state.modelo_a}")
            if not st.session_state.suc_b: 
                detalhes.append(f"❌ {st.session_state.modelo_b}")
            st.text("Modelos com erro:\n" + "\n".join(detalhes))