"""
Listar Modelos Disponíveis — OpenAI, NVIDIA, Google Gemini
Roda com: streamlit run listar_modelos.py
"""
import streamlit as st
from openai import OpenAI
import google.generativeai as genai

st.set_page_config(page_title="Listar Modelos", page_icon="📋", layout="wide")
st.title("📋 Modelos Disponíveis por API")

# ============================================================
# 1. OpenAI
# ============================================================
st.header("1️⃣ OpenAI")
if "OPENAI_API_KEY" in st.secrets:
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        models = sorted(client.models.list(), key=lambda m: m.id)
        
        vision_keywords = ["gpt-4o", "gpt-4-turbo", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-5", "gpt-5-mini"]
        
        data = []
        for m in models:
            is_multi = any(kw in m.id for kw in vision_keywords)
            data.append({
                "Modelo": m.id,
                "Multimodal (Imagem)": "✅ Sim" if is_multi else "❌ Não"
            })
        
        st.success(f"✅ Conectado! {len(models)} modelos encontrados.")
        st.dataframe(data, width='stretch', hide_index=True)
    except Exception as e:
        st.error(f"Erro OpenAI: {e}")
else:
    st.warning("⚠️ OPENAI_API_KEY não configurada.")

st.divider()

# ============================================================
# 2. NVIDIA (NIM)
# ============================================================
st.header("2️⃣ NVIDIA (NIM)")
if "NVIDIA_API_KEY" in st.secrets:
    try:
        client = OpenAI(
            api_key=st.secrets["NVIDIA_API_KEY"],
            base_url="https://integrate.api.nvidia.com/v1"
        )
        models = sorted(client.models.list(), key=lambda m: m.id)
        
        # Modelos conhecidos como multimodais (Image-to-Text)
        vision_known = [
            "llama-3.2-90b-vision", "llama-3.2-11b-vision",
            "llama-4-maverick", "llama-4-scout",
            "kimi-k2.5", "phi-4-multimodal", "phi-3.5-vision",
            "gemma-3-27b", "mistral-large-3-675b", "ministral-14b",
            "mistral-medium-3", "neva"
        ]
        
        data = []
        for m in models:
            is_multi = any(kw in m.id for kw in vision_known)
            data.append({
                "Modelo": m.id,
                "Multimodal (Imagem)": "✅ Sim" if is_multi else "❌ Não"
            })
        
        st.success(f"✅ Conectado! {len(models)} modelos encontrados.")
        
        # Filtro
        filtro = st.radio("Filtrar:", ["Todos", "Só Multimodais"], horizontal=True, key="nvidia_filter")
        if filtro == "Só Multimodais":
            data = [d for d in data if d["Multimodal (Imagem)"] == "✅ Sim"]
        
        st.dataframe(data, width='stretch', hide_index=True)
    except Exception as e:
        st.error(f"Erro NVIDIA: {e}")
else:
    st.warning("⚠️ NVIDIA_API_KEY não configurada.")

st.divider()

# ============================================================
# 3. Google Gemini
# ============================================================
st.header("3️⃣ Google Gemini")
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = genai.list_models()
        
        data = []
        for m in models:
            methods = m.supported_generation_methods if hasattr(m, 'supported_generation_methods') else []
            is_multi = "generateContent" in methods
            data.append({
                "Modelo": m.name,
                "Multimodal (Imagem)": "✅ Sim" if is_multi else "❌ Não",
                "Métodos": ", ".join(methods) if methods else "—"
            })
        
        st.success(f"✅ Conectado! {len(data)} modelos encontrados.")
        
        filtro = st.radio("Filtrar:", ["Todos", "Só Multimodais"], horizontal=True, key="gemini_filter")
        if filtro == "Só Multimodais":
            data = [d for d in data if d["Multimodal (Imagem)"] == "✅ Sim"]
        
        st.dataframe(data, width='stretch', hide_index=True)
    except Exception as e:
        st.error(f"Erro Gemini: {e}")
else:
    st.warning("⚠️ GOOGLE_API_KEY não configurada.")