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

from utils.session import init
from ai.models import executar_analise_cached
from ai.schemas import AnaliseBiologica

st.set_page_config(page_title="Teste Structured Outputs", layout="wide")
st.title("🛡️ Teste de Saída Estruturada (Schema Pydantic)")

# Imagem de teste (Pixel Vermelho) - JPEG (Validada)
PIXEL_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
IMG_HASH = "test_hash_red_pixel"

from utils.session import init

# Inicializa sessão para carregar modelos do secrets
init()

if st.button("Iniciar Teste de Schema"):
    st.write("Iniciando testes... (Isso pode consumir tokens)")
    
    # Recupera modelos da sessão
    modelos_dict = st.session_state.get("modelos_disponiveis", {})
    
    if not modelos_dict:
        st.error("Nenhum modelo encontrado no Session State. Verifique seus secrets.")
        st.stop()

    results = []
    
    # Itera sobre todos os modelos carregados dinamicamente
    for nome, tipo in modelos_dict.items():
        # Define provedor baseado no tipo
        provider = "Desconhecido"
        if tipo == 1: provider = "OpenAI"
        elif tipo == 2: provider = "Google Gemini"
        elif tipo == 4: provider = "NVIDIA NIM"
        
        st.write(f"### Testando {provider}: `{nome}`")
        
        # Como o init() já filtra por chaves existentes, não precisamos checar secrets aqui novamente

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
