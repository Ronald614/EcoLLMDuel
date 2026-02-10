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


@st.cache_data(ttl=3600, show_spinner=False)
def executar_analise_cached(nome_modelo: str, prompt: str, img_hash: str, img_codificada: str, tipo: int):
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
                keys = []
                if "GOOGLE_API_KEY" in st.secrets: keys.append(st.secrets["GOOGLE_API_KEY"])
                if "GOOGLE_API_KEY_2" in st.secrets: keys.append(st.secrets["GOOGLE_API_KEY_2"])
                
                if not keys:
                    raise Exception("Nenhuma chave Gemini configurada.")

                last_error = None
                for i, api_key in enumerate(keys):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(nome_modelo)
                        config_simples = {
                            "temperature": TEMPERATURA_FIXA,
                            "max_output_tokens": LIMITE_TOKENS,
                        }
                        
                        blob = {"mime_type": "image/jpeg", "data": img_codificada}
                        r = model.generate_content(
                            [prompt, blob],
                            generation_config=config_simples
                        )
                        resp = r.text
                        last_error = None
                        break
                        
                    except Exception as e:
                        print(f"⚠️ [GEMINI] Chave {i+1} falhou: {e}")
                        last_error = e
                        if i < len(keys) - 1:
                            print(f"🔄 Tentando próxima chave...")
                            continue
                
                if last_error:
                    raise last_error



            elif tipo == 4:
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

def executar_analise(nome_modelo, prompt, imagem, img_codificada):
    tipo = st.session_state.modelos_disponiveis.get(nome_modelo)
    img_hash = hashlib.md5(img_codificada.encode()).hexdigest()
    return executar_analise_cached(nome_modelo, prompt, img_hash, img_codificada, tipo)