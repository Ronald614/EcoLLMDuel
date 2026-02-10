"""
Ping de Modelos — Testa conectividade com todos os modelos configurados.
Usa max_tokens=1 para consumir o mínimo de tokens possível.
Roda com: streamlit run ping_modelos.py
"""
import streamlit as st
import time
from openai import OpenAI
import google.generativeai as genai

st.set_page_config(page_title="Ping Modelos", page_icon="🏓", layout="wide")
st.title("🏓 Ping de Modelos")
st.caption("Testa se cada modelo responde. Usa max_tokens=1 para economizar tokens.")

# Modelos organizados por API
modelos = {}

# OpenAI (Tipo 1)
if "OPENAI_API_KEY" in st.secrets:
    for m in ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4-turbo"]:
        modelos[m] = "openai"

# NVIDIA (Tipo 4)
if "NVIDIA_API_KEY" in st.secrets:
    for m in [
        "meta/llama-3.2-90b-vision-instruct",
        "meta/llama-3.2-11b-vision-instruct",
        "meta/llama-4-maverick-17b-128e-instruct",
        "meta/llama-4-scout-17b-16e-instruct",
        "mistralai/mistral-large-3-675b-instruct-2512",
        "mistralai/ministral-14b-instruct-2512",
        "mistralai/mistral-medium-3-instruct",
        "microsoft/phi-4-multimodal-instruct",
        "microsoft/phi-3.5-vision-instruct",
        "google/gemma-3-27b-it",
        "moonshotai/kimi-k2.5",
    ]:
        modelos[m] = "nvidia"

# Google Gemini (Tipo 2)
if "GOOGLE_API_KEY" in st.secrets:
    for m in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]:
        modelos[m] = "gemini"

st.info(f"📋 {len(modelos)} modelos para testar.")

def ping_openai(nome_modelo):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    client.chat.completions.create(
        model=nome_modelo,
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1
    )

def ping_nvidia(nome_modelo):
    client = OpenAI(
        api_key=st.secrets["NVIDIA_API_KEY"],
        base_url="https://integrate.api.nvidia.com/v1"
    )
    client.chat.completions.create(
        model=nome_modelo,
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1
    )

def ping_gemini(nome_modelo):
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(nome_modelo)
    model.generate_content("ping", generation_config={"max_output_tokens": 1})

if st.button("🚀 Iniciar Ping", type="primary"):
    resultados = []
    progresso = st.progress(0, text="Iniciando...")
    
    for i, (nome, api) in enumerate(modelos.items()):
        progresso.progress((i) / len(modelos), text=f"Pingando {nome}...")
        
        inicio = time.time()
        status = "✅ OK"
        erro = ""
        
        try:
            if api == "openai":
                ping_openai(nome)
            elif api == "nvidia":
                ping_nvidia(nome)
            elif api == "gemini":
                ping_gemini(nome)
        except Exception as e:
            status = "❌ ERRO"
            erro = str(e)[:200]
            print(f"❌ [PING] {nome}: {erro}")
        
        tempo = time.time() - inicio
        resultados.append({
            "Modelo": nome,
            "API": api.upper(),
            "Status": status,
            "Tempo (s)": f"{tempo:.2f}",
            "Erro": erro
        })
    
    progresso.progress(1.0, text="Concluído!")
    
    # Resumo
    ok = sum(1 for r in resultados if r["Status"] == "✅ OK")
    falhas = sum(1 for r in resultados if r["Status"] == "❌ ERRO")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(resultados))
    col2.metric("✅ OK", ok)
    col3.metric("❌ Falhas", falhas)
    
    # Tabela de resultados
    st.dataframe(resultados, width='stretch', hide_index=True)
    
    # Log de erros detalhados
    erros = [r for r in resultados if r["Status"] == "❌ ERRO"]
    if erros:
        st.divider()
        st.subheader("📛 Detalhes dos Erros")
        for e in erros:
            st.error(f"**{e['Modelo']}** ({e['API']}): {e['Erro']}")
