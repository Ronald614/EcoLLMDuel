"""
Diagnóstico de Chaves Gemini — Testa conectividade com os modelos do EcoLLMDuel.
Roda com: env/bin/streamlit run test_gemini_keys.py
"""
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Teste Gemini", page_icon="🔑")
st.title("🔑 Diagnóstico de Chaves Gemini")

# Modelos exatos usados no session.py (Tipo 2)
MODELOS = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite"]

# Chaves disponíveis
chaves = {}
if "GOOGLE_API_KEY" in st.secrets:
    chaves["GOOGLE_API_KEY (Principal)"] = st.secrets["GOOGLE_API_KEY"]
if "GOOGLE_API_KEY_2" in st.secrets:
    chaves["GOOGLE_API_KEY_2 (Secundária)"] = st.secrets["GOOGLE_API_KEY_2"]

if not chaves:
    st.error("❌ Nenhuma chave Gemini encontrada no secrets.toml!")
    st.stop()

st.info(f"🔑 {len(chaves)} chave(s) encontrada(s). Testando {len(MODELOS)} modelos cada...")

for nome_chave, valor_chave in chaves.items():
    st.subheader(f"🔑 {nome_chave}")
    genai.configure(api_key=valor_chave)

    for modelo_nome in MODELOS:
        with st.spinner(f"Testando {modelo_nome}..."):
            try:
                model = genai.GenerativeModel(modelo_nome)
                r = model.generate_content("Diga apenas: OK", generation_config={"max_output_tokens": 5})
                st.success(f"✅ `{modelo_nome}` → {r.text.strip()}")
                print(f"✅ {nome_chave} | {modelo_nome} → OK")
            except Exception as e:
                st.error(f"❌ `{modelo_nome}` → {e}")
                print(f"❌ {nome_chave} | {modelo_nome} → {e}")

st.divider()
st.caption("Teste concluído.")
