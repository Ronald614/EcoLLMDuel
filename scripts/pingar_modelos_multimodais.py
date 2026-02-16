"""
Script consolidado para descobrir e testar modelos OpenAI Multimodais.
Filtra modelos datados/temporários e aqueles incompatíveis com Chat Completions API.
Automáticamente gera a configuração para utils/session.py.
"""
import streamlit as st
from openai import OpenAI
import base64
from io import BytesIO
from PIL import Image
import re

st.set_page_config(page_title="Pingar Modelos Multimodais", page_icon=None, layout="wide")
st.title("Ping de Modelos Multimodais (OpenAI)")
st.info("Este script descobre modelos, filtra versões datadas/temporárias e testa suporte a visão.")

# --- Config: Imagem de Teste (1x1 pixel vermelho) ---
PIXEL_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
DATA_URL = f"data:image/png;base64,{PIXEL_B64}"

if st.button("Iniciar Descoberta e Teste"):
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("OPENAI_API_KEY não encontrada no secrets.toml")
        st.stop()

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    with st.spinner("Listando e filtrando modelos..."):
        all_models = client.models.list()
        candidates = []
        
        # Regex para identificar datas (ex: 2024-05-13)
        date_pattern = re.compile(r"-\d{4}-\d{2}-\d{2}")

        for m in all_models:
            mid = m.id
            # Critérios de inclusão: gpt-* ou o1-*
            if not (mid.startswith("gpt-") or mid.startswith("o1-")):
                continue
            
            # Critérios de exclusão:
            if "audio" in mid or "realtime" in mid:
                continue
            
            # Filtra versões datadas (ex: gpt-4o-2024-05-13).
            # Remove qualquer modelo que contenha padrão de data,
            # mantendo apenas as versões estáveis (ex: gpt-4o, gpt-4o-mini).
            if date_pattern.search(mid):
                continue
                
            candidates.append(mid)
        
        candidates.sort()
    
    st.write(f"Candidatos selecionados (sem datas): {len(candidates)}")
    st.code(", ".join(candidates))
    
    results = []
    progress_bar = st.progress(0)
    
    for i, model_id in enumerate(candidates):
        token_param = "max_completion_tokens" if (model_id.startswith("o1-") or model_id.startswith("gpt-5")) else "max_tokens"
        
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Color?"},
                            {"type": "image_url", "image_url": {"url": DATA_URL}},
                        ],
                    }
                ],
                **{token_param: 50} # Aumentado para 50 tokens para evitar erros em modelos verbosos
            )
            res_content = response.choices[0].message.content
            results.append({"Modelo": model_id, "Status": "Aprovado", "Info": "Vision OK", "Resposta": res_content})
            
        except Exception as e:
            err_msg = str(e)
            if "This model is only supported in v1/responses" in err_msg:
                 results.append({"Modelo": model_id, "Status": "Ignorado", "Info": "Não suporta Chat API (v1/responses only)", "Resposta": ""})
            elif "does not support image" in err_msg:
                 results.append({"Modelo": model_id, "Status": "Aprovado (Texto)", "Info": "Vision não suportado, mas Chat OK", "Resposta": ""})
            else:
                 results.append({"Modelo": model_id, "Status": "Erro", "Info": err_msg[:100], "Resposta": ""})
        
        progress_bar.progress((i + 1) / len(candidates))

    progress_bar.empty()
    st.divider()
    
    # Exibir Aprovados e gerar Config
    approved = [r for r in results if r["Status"] == "Aprovado"]
    
    if approved:
        st.success(f"{len(approved)} modelos aprovados para uso Multimodal!")
        
        config_code = "modelos = {}\n"
        for item in approved:
            config_code += f'modelos["{item["Modelo"]}"] = 1\n'
            
        st.code(config_code, language="python")
    else:
        st.warning("Nenhum modelo passou no teste de visão.")
    
    st.subheader("Detalhes de todos os testes")
    st.dataframe(results, width="stretch")
