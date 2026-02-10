import time
import hashlib
import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from config import TEMPERATURA_FIXA, LIMITE_TOKENS

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])



@st.cache_resource
def get_nvidia_client():
    return OpenAI(
        api_key=st.secrets["NVIDIA_API_KEY"], 
        base_url="https://integrate.api.nvidia.com/v1"
    )

@st.cache_resource
def get_gemini_config():
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    return genai

@st.cache_data(ttl=3600, show_spinner=False)
def executar_analise_cached(nome_modelo: str, prompt: str, img_hash: str, img_codificada: str, tipo: int):
    """Versão cacheável de executar_analise. Cache de 1 hora."""
    start = time.time()
    max_retries = 2
    tempo_espera = 20

    for tentativa in range(max_retries):
        try:
            resp = ""

            if tipo == 1:
                client = get_openai_client()
                r = client.chat.completions.create(
                    model=nome_modelo,
                    messages=[{
                        "role":"user",
                        "content":[
                            {"type":"text","text":prompt},
                            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                        ]
                    }],
                    temperature=TEMPERATURA_FIXA,
                    max_tokens=LIMITE_TOKENS
                )
                resp = r.choices[0].message.content

            elif tipo == 2:
                genai_client = get_gemini_config()
                model = genai_client.GenerativeModel(nome_modelo)
                config_simples = {
                    "temperature": TEMPERATURA_FIXA,
                    "max_output_tokens": LIMITE_TOKENS,
                }
                r = model.generate_content(
                    [prompt, img_codificada],
                    generation_config=config_simples
                )
                resp = r.text



            elif tipo == 4:
                # NVIDIA API (NIM)
                client = get_nvidia_client()
                r = client.chat.completions.create(
                    model=nome_modelo,
                    messages=[{
                        "role":"user",
                        "content":[
                            {"type":"text","text":prompt},
                            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                        ]
                    }],
                    temperature=TEMPERATURA_FIXA,
                    max_tokens=LIMITE_TOKENS
                )
                resp = r.choices[0].message.content

            return True, resp, time.time() - start

        except Exception as e:
            erro_msg = str(e)

            if ("429" in erro_msg or "quota" in erro_msg or "exhausted" in erro_msg) and tentativa < max_retries - 1:
                print(f"⚠️ [LOG] Cota excedida no {nome_modelo}. Tentativa {tentativa+1}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue

            print(f"❌ [LOG] Erro fatal no modelo {nome_modelo}: {erro_msg}")
            return False, None, time.time() - start

    print(f"❌ [LOG] Falha total no modelo {nome_modelo} após {max_retries} tentativas.")
    return False, None, time.time() - start

def executar_analise(nome_modelo, prompt, imagem, img_codificada, show_spinner=True):
    """Wrapper que calcula hash da imagem e chama versão cacheada."""
    tipo = st.session_state.modelos_disponiveis.get(nome_modelo)
    img_hash = hashlib.md5(img_codificada.encode()).hexdigest()
    
    if show_spinner:
        return executar_analise_cached(nome_modelo, prompt, img_hash, img_codificada, tipo)
    else:
        # Desativa o spinner interno do cache
        return executar_analise_cached(nome_modelo, prompt, img_hash, img_codificada, tipo)