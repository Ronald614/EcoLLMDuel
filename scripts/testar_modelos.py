"""
Testar Modelos — Lê session.py e testa cada modelo com envio de imagem.
Roda com: streamlit run scripts/testar_modelos.py
"""
import os, re, time
import streamlit as st
from openai import OpenAI
import google.generativeai as genai

st.set_page_config(page_title="Testar Modelos", page_icon="🧪", layout="wide")
st.title("🧪 Testar Modelos do App")
st.caption("Lê os modelos configurados em `utils/session.py` e testa cada um contra as chaves de API disponíveis.")

# --- Pixel 1x1 vermelho para teste de visão ---
PIXEL_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
DATA_URL = f"data:image/png;base64,{PIXEL_B64}"

# ============================================================
# Ler modelos de session.py (sem importar)
# ============================================================
_session_path = os.path.join(os.path.dirname(__file__), "..", "utils", "session.py")
with open(_session_path) as f:
    _src = f.read()

# Extrai modelos ativos e comentados
modelos_ativos = {}  # nome -> tipo
for m in re.finditer(r'^\s+modelos\["([^"]+)"\]\s*=\s*(\d+)', _src, re.MULTILINE):
    modelos_ativos[m.group(1)] = int(m.group(2))

modelos_comentados = {}
for m in re.finditer(r'^\s*#\s*modelos\["([^"]+)"\]\s*=\s*(\d+)', _src, re.MULTILINE):
    modelos_comentados[m.group(1)] = int(m.group(2))


# ============================================================
# Montar chaves disponíveis
# ============================================================
chaves = {}  # "label" -> {tipo, client_factory ou api_key}

# OpenAI
openai_keys = {}
if "OPENAI_API_KEY" in st.secrets:
    openai_keys["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "OPENAI_API_KEY_2" in st.secrets:
    openai_keys["OPENAI_API_KEY_2"] = st.secrets["OPENAI_API_KEY_2"]

# Google
google_keys = {}
if "GOOGLE_API_KEY" in st.secrets:
    google_keys["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
if "GOOGLE_API_KEY_2" in st.secrets:
    google_keys["GOOGLE_API_KEY_2"] = st.secrets["GOOGLE_API_KEY_2"]

# NVIDIA
nvidia_keys = {}
if "NVIDIA_API_KEY" in st.secrets:
    nvidia_keys["NVIDIA_API_KEY"] = st.secrets["NVIDIA_API_KEY"]


# ============================================================
# Helpers de teste
# ============================================================
def testar_openai(client, model_id):
    """Testa um modelo OpenAI com envio de imagem. Retorna (status, info)."""
    token_param = "max_completion_tokens" if (model_id.startswith("o1-") or "gpt-5" in model_id) else "max_tokens"
    try:
        r = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "What color is this pixel?"},
                {"type": "image_url", "image_url": {"url": DATA_URL}},
            ]}],
            **{token_param: 200}
        )
        return "✅ OK", r.choices[0].message.content[:80]
    except Exception as e:
        msg = str(e)
        if "v1/responses" in msg:
            return "⏭️ Ignorado", "Só suporta v1/responses"
        if "does not support image" in msg:
            return "⚠️ Sem visão", "Chat funciona mas sem imagem"
        return "❌ Erro", msg[:100]


def testar_nvidia(client, model_id):
    """Testa um modelo NVIDIA com envio de imagem."""
    try:
        r = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "What color is this pixel?"},
                {"type": "image_url", "image_url": {"url": DATA_URL}},
            ]}],
            max_tokens=50, temperature=0.5
        )
        return "✅ OK", r.choices[0].message.content[:80]
    except Exception as e:
        return "❌ Erro", str(e)[:100]


def testar_gemini(api_key, model_id):
    """Testa um modelo Gemini com envio de imagem."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)
        blob = {"mime_type": "image/png", "data": PIXEL_B64}
        r = model.generate_content(
            ["What color is this pixel?", blob],
            generation_config={"max_output_tokens": 50}
        )
        return "✅ OK", r.text[:80]
    except Exception as e:
        return "❌ Erro", str(e)[:100]


# ============================================================
# Resumo do que foi lido
# ============================================================
st.subheader("📄 Modelos lidos de `session.py`")

col1, col2 = st.columns(2)
with col1:
    st.metric("Ativos", len(modelos_ativos))
with col2:
    st.metric("Comentados", len(modelos_comentados))

with st.expander("Ver lista completa"):
    for nome, tipo in sorted(modelos_ativos.items()):
        tp = {1: "OpenAI", 2: "Gemini", 4: "NVIDIA"}.get(tipo, f"Tipo {tipo}")
        st.write(f"🟢 `{nome}` — {tp}")
    for nome, tipo in sorted(modelos_comentados.items()):
        tp = {1: "OpenAI", 2: "Gemini", 4: "NVIDIA"}.get(tipo, f"Tipo {tipo}")
        st.write(f"💤 `{nome}` — {tp} *(comentado)*")

st.divider()

# ============================================================
# Chaves detectadas
# ============================================================
st.subheader("🔑 Chaves de API detectadas")
cols = st.columns(3)
with cols[0]:
    for k in openai_keys:
        st.success(f"OpenAI: `{k}`")
    if not openai_keys:
        st.warning("Nenhuma chave OpenAI")
with cols[1]:
    for k in google_keys:
        st.success(f"Google: `{k}`")
    if not google_keys:
        st.warning("Nenhuma chave Google")
with cols[2]:
    for k in nvidia_keys:
        st.success(f"NVIDIA: `{k}`")
    if not nvidia_keys:
        st.warning("Nenhuma chave NVIDIA")

st.divider()

# ============================================================
# Teste
# ============================================================
incluir_comentados = st.checkbox("Incluir modelos comentados no teste", value=False)
modelos_para_testar = dict(modelos_ativos)
if incluir_comentados:
    modelos_para_testar.update(modelos_comentados)

if st.button("🚀 Iniciar Testes", type="primary"):
    # Separar por tipo
    openai_models = {n for n, t in modelos_para_testar.items() if t == 1}
    gemini_models = {n for n, t in modelos_para_testar.items() if t == 2}
    nvidia_models = {n for n, t in modelos_para_testar.items() if t == 4}

    total = (len(openai_models) * len(openai_keys) +
             len(gemini_models) * len(google_keys) +
             len(nvidia_models) * len(nvidia_keys))
    
    if total == 0:
        st.warning("Nenhum modelo/chave para testar.")
        st.stop()

    progress = st.progress(0)
    done = 0
    all_results = []

    # --- OpenAI ---
    if openai_models and openai_keys:
        st.subheader("🔵 OpenAI")
        for key_name, key_value in openai_keys.items():
            st.markdown(f"**🔑 `{key_name}`**")
            client = OpenAI(api_key=key_value)
            results = []
            for model_id in sorted(openai_models):
                status, info = testar_openai(client, model_id)
                results.append({"Modelo": model_id, "Status": status, "Resposta": info})
                done += 1
                progress.progress(done / total)
            st.dataframe(results, width='stretch', hide_index=True)
            all_results.extend([(key_name, r) for r in results])

    # --- Gemini ---
    if gemini_models and google_keys:
        st.subheader("🟡 Google Gemini")
        for key_name, key_value in google_keys.items():
            st.markdown(f"**🔑 `{key_name}`**")
            results = []
            for model_id in sorted(gemini_models):
                status, info = testar_gemini(key_value, model_id)
                results.append({"Modelo": model_id, "Status": status, "Resposta": info})
                done += 1
                progress.progress(done / total)
            st.dataframe(results, width='stretch', hide_index=True)
            all_results.extend([(key_name, r) for r in results])

    # --- NVIDIA ---
    if nvidia_models and nvidia_keys:
        st.subheader("🟢 NVIDIA")
        for key_name, key_value in nvidia_keys.items():
            st.markdown(f"**🔑 `{key_name}`**")
            client = OpenAI(api_key=key_value, base_url="https://integrate.api.nvidia.com/v1")
            results = []
            for model_id in sorted(nvidia_models):
                status, info = testar_nvidia(client, model_id)
                results.append({"Modelo": model_id, "Status": status, "Resposta": info})
                done += 1
                progress.progress(done / total)
            st.dataframe(results, width='stretch', hide_index=True)
            all_results.extend([(key_name, r) for r in results])

    progress.empty()
    st.divider()

    # --- Resumo ---
    st.subheader("📊 Resumo")
    ok = sum(1 for _, r in all_results if r["Status"] == "✅ OK")
    erros = sum(1 for _, r in all_results if r["Status"] == "❌ Erro")
    outros = len(all_results) - ok - erros

    c1, c2, c3 = st.columns(3)
    c1.metric("✅ OK", ok)
    c2.metric("❌ Erros", erros)
    c3.metric("⏭️ Outros", outros)

    # Comparação entre chaves OpenAI
    if len(openai_keys) == 2 and openai_models:
        st.subheader("🔍 Comparação entre chaves OpenAI")
        nomes = list(openai_keys.keys())
        status_por_chave = {n: {} for n in nomes}
        for key_name, r in all_results:
            if key_name in nomes:
                status_por_chave[key_name][r["Modelo"]] = r["Status"]
        
        comp = []
        for modelo in sorted(openai_models):
            s0 = status_por_chave[nomes[0]].get(modelo, "—")
            s1 = status_por_chave[nomes[1]].get(modelo, "—")
            iguais = "✅" if s0 == s1 else "⚠️"
            comp.append({"Modelo": modelo, nomes[0]: s0, nomes[1]: s1, "Match": iguais})
        
        st.dataframe(comp, width='stretch', hide_index=True)
        
        divergentes = [c for c in comp if c["Match"] == "⚠️"]
        if divergentes:
            st.warning(f"{len(divergentes)} modelo(s) com resultado diferente entre as chaves!")
        else:
            st.success("Ambas as chaves produzem resultados idênticos para todos os modelos!")
