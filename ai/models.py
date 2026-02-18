import time
import hashlib
import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from config import TEMPERATURA_FIXA, LIMITE_TOKENS
from ai.schemas import AnaliseBiologica

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
                # Modelos novos (gpt-5*) usam max_completion_tokens
                token_param = "max_completion_tokens" if "gpt-5" in nome_modelo else "max_tokens"
                
                # Alguns modelos novos não permitem temperatura != 1
                kwargs = {token_param: LIMITE_TOKENS}
                if not ("gpt-5" in nome_modelo or "o1" in nome_modelo):
                    kwargs["temperature"] = TEMPERATURA_FIXA

                try:
                    # Structured Outputs (SDK recente)
                    r = client.beta.chat.completions.parse(
                        model=nome_modelo,
                        messages=[{
                            "role":"user",
                            "content":[
                                {"type":"text","text":prompt},
                                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                            ]
                        }],
                        response_format=AnaliseBiologica,
                        **kwargs
                    )
                    # Manter compatibilidade
                    resp = r.choices[0].message.parsed.model_dump_json()
                    
                except Exception as e_struct:
                    print(f"Erro ao usar Structured Outputs: {e_struct}. Tentando fallback JSON Mode.")
                    # Fallback para JSON Mode
                    r = client.chat.completions.create(
                        model=nome_modelo,
                        messages=[{
                            "role":"user",
                            "content":[
                                {"type":"text","text":prompt},
                                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                            ]
                        }],
                        response_format={"type": "json_object"},
                        **kwargs
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
                            "response_mime_type": "application/json",
                            "response_schema": AnaliseBiologica
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
                        print(f"[GEMINI] Chave {i+1} falhou: {e}")
                        last_error = e
                        if i < len(keys) - 1:
                            print(f"Tentando próxima chave...")
                            continue
                
                if last_error:
                    raise last_error



            elif tipo == 4:
                client = get_nvidia_client()
                r = client.chat.completions.create(
                    model=nome_modelo,
                    messages=[{
                        "role": "system",
                         "content": "You are a specialized biology assistant. You MUST output ONLY a valid JSON object matching the schema. Do not include markdown formatting (```json), explanations, or any other text."
                    }, {
                        "role":"user",
                        "content":[
                            {"type":"text","text":prompt},
                            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                        ]
                    }],
                    temperature=TEMPERATURA_FIXA,
                    max_tokens=LIMITE_TOKENS,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "AnaliseBiologica",
                            "schema": AnaliseBiologica.model_json_schema()
                        }
                    }
                )
                resp = r.choices[0].message.content

            print(f"[LOG] Sucesso no modelo {nome_modelo} em {(time.time() - start):.2f}s")
            return True, resp, time.time() - start

        except Exception as e:
            erro_msg = str(e)

            if ("429" in erro_msg or "quota" in erro_msg or "exhausted" in erro_msg) and tentativa < max_retries - 1:
                print(f"[LOG] Cota excedida no {nome_modelo}. Tentativa {tentativa+1}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue

            print(f"[LOG] Erro fatal no modelo {nome_modelo}: {erro_msg}")
            return False, None, time.time() - start

    print(f"[LOG] Falha total no modelo {nome_modelo} após {max_retries} tentativas.")
    return False, None, time.time() - start

def executar_analise(nome_modelo, prompt, imagem, img_codificada):
    tipo = st.session_state.modelos_disponiveis.get(nome_modelo)
    img_hash = hashlib.sha256(img_codificada.encode()).hexdigest()
    return executar_analise_cached(nome_modelo, prompt, img_hash, img_codificada, tipo)