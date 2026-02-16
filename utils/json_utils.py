import json
import re
import streamlit as st

def extrair_json(texto: str) -> dict | None:
    """Extrai JSON da resposta. Como usamos JSON Mode, a resposta já deve vir limpa."""
    texto = texto.strip()
    
    # Remover markdown se houver (ex: ```json ... ```)
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\n?|\n?```$", "", texto, flags=re.MULTILINE)
    
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return None

def decodificar_json(resposta: str) -> bool:
    """Tenta renderizar o JSON na interface."""
    dados = extrair_json(resposta)
    if dados:
        st.json(dados)
        return True
    
    st.warning("O modelo não retornou um JSON válido.")
    st.code(resposta, language="text")
    return False