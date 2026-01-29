import streamlit as st
from openai import OpenAI
import google.generativeai as genai

# Configuração da página
st.set_page_config(page_title="Verificador de Modelos", page_icon="🔍")
st.title("🔍 Verificador de Modelos Disponíveis")

def list_openai_models():
    """Busca e exibe os modelos disponíveis da OpenAI."""
    st.header("OpenAI")
    
    # Tenta pegar a chave do secrets.toml
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except KeyError:
        st.error("❌ Chave 'OPENAI_API_KEY' não encontrada no secrets.toml")
        return

    try:
        client = OpenAI(api_key=api_key)
        models_list = client.models.list()
        
        st.success(f"✅ Conectado! Encontrados {len(list(models_list))} modelos.")
        
        # Cria uma lista expansível para não poluir a tela
        with st.expander("Ver lista completa da OpenAI"):
            # A API retorna um objeto paginado, iteramos sobre ele
            for model in sorted(models_list, key=lambda m: m.id):
                st.code(model.id, language="text")
                
    except Exception as e:
        st.error(f"Erro ao conectar na OpenAI: {e}")

def list_gemini_models():
    """Busca e exibe os modelos disponíveis do Google Gemini."""
    st.header("Google Gemini")

    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("❌ Chave 'GOOGLE_API_KEY' não encontrada no secrets.toml")
        return

    try:
        genai.configure(api_key=api_key)
        
        st.write("Modelos que suportam geração de conteúdo:")
        modelos_encontrados = []
        
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                modelos_encontrados.append(model.name)
        
        st.success(f"✅ Conectado! Encontrados {len(modelos_encontrados)} modelos compatíveis.")
        
        with st.expander("Ver lista completa do Gemini"):
            for nome in sorted(modelos_encontrados):
                st.code(nome, language="text")
                
    except Exception as e:
        st.error(f"Erro ao conectar no Google Gemini: {e}")

def list_deepseek_models():
    """Busca e exibe os modelos disponíveis da DeepSeek."""
    st.header("DeepSeek")

    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except KeyError:
        st.error("❌ Chave 'DEEPSEEK_API_KEY' não encontrada no secrets.toml")
        return

    try:
        # DeepSeek usa a mesma lib da OpenAI, mas com base_url diferente
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        models_list = client.models.list()
        
        st.success(f"✅ Conectado! Encontrados modelos.")
        
        with st.expander("Ver lista completa da DeepSeek"):
            for model in sorted(models_list, key=lambda m: m.id):
                st.code(model.id, language="text")
                
    except Exception as e:
        st.error(f"Erro ao conectar na DeepSeek: {e}")

if __name__ == "__main__":
    # Botão para rodar a verificação
    if st.button("🔄 Listar Todos os Modelos Agora", type="primary"):
        list_openai_models()
        st.divider()
        list_gemini_models()
        st.divider()
        list_deepseek_models()
    else:
        st.info("Clique no botão acima para buscar os modelos usando suas chaves do secrets.toml")