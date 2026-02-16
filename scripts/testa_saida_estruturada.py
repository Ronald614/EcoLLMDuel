"""
Script para testar a Saída Estruturada (Structured Outputs) em todos os provedores.
Verifica se ai.models.executar_analise_cached retorna JSON válido e aderente ao Schema.
"""
import streamlit as st
import sys
import os
import base64
from io import BytesIO
from PIL import Image

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.models import executar_analise_cached
from ai.schemas import AnaliseBiologica

st.set_page_config(page_title="Teste Structured Outputs", layout="wide")
st.title("🛡️ Teste de Saída Estruturada (Schema Pydantic)")

# Imagem de teste (Pixel Vermelho) - JPEG
PIXEL_B64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD/2Q=="
IMG_HASH = "test_hash_red_pixel"

# Modelos para testar (Um de cada tipo se possível)
modelos_teste = [
    {"nome": "gpt-4o-mini", "tipo": 1, "provider": "OpenAI"},
    {"nome": "gemini-2.5-flash", "tipo": 2, "provider": "Google Gemini"}, # Usando versão estável recente
    {"nome": "meta/llama-3.2-11b-vision-instruct", "tipo": 4, "provider": "NVIDIA NIM"},
]

if st.button("Iniciar Teste de Schema"):
    st.write("Iniciando testes... (Isso pode consumir tokens)")
    
    results = []
    
    for m in modelos_teste:
        nome = m["nome"]
        tipo = m["tipo"]
        provider = m["provider"]
        
        st.write(f"### Testando {provider}: `{nome}`")
        
        # Verifica chaves antes de tentar
        msg_skip = None
        if tipo == 1 and "OPENAI_API_KEY" not in st.secrets:
            msg_skip = "OPENAI_API_KEY ausente"
        elif tipo == 2 and "GOOGLE_API_KEY" not in st.secrets:
             msg_skip = "GOOGLE_API_KEY ausente"
        elif tipo == 4 and "NVIDIA_API_KEY" not in st.secrets:
             msg_skip = "NVIDIA_API_KEY ausente"
             
        if msg_skip:
            st.warning(f"Pulando {nome}: {msg_skip}")
            results.append({"Modelo": nome, "Provedor": provider, "Status": "Skipped", "Erro": msg_skip, "JSON": ""})
            continue

        try:
            sucesso, resp_json, tempo = executar_analise_cached(
                nome_modelo=nome,
                prompt="Analise esta imagem. Responda em JSON estrito.",
                img_hash=IMG_HASH,
                img_codificada=PIXEL_B64,
                tipo=tipo
            )
            
            if sucesso:
                st.success(f"Sucesso! ({tempo:.2f}s)")
                st.json(resp_json)
                results.append({"Modelo": nome, "Provedor": provider, "Status": "Passou", "Erro": "", "JSON": resp_json})
            else:
                st.error("Falha na execução.")
                results.append({"Modelo": nome, "Provedor": provider, "Status": "Falhou", "Erro": "Retornou False", "JSON": ""})
                
        except Exception as e:
            st.error(f"Erro: {e}")
            results.append({"Modelo": nome, "Provedor": provider, "Status": "Erro", "Erro": str(e), "JSON": ""})
            
    st.subheader("Resumo")
    st.dataframe(results)
