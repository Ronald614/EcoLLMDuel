import json
import re
import streamlit as st

def extrair_json(texto: str) -> dict | None:
    """Tenta extrair JSON de uma string que pode conter texto ao redor."""
    texto_limpo = texto.strip()
    
    # 1. Remover blocos markdown ```json ... ```
    match_md = re.search(r'```(?:json)?\s*(.*?)\s*```', texto_limpo, re.DOTALL)
    if match_md:
        texto_limpo = match_md.group(1).strip()
    
    # 2. Tentar parse direto
    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError:
        # 3. Último recurso: procurar JSON dentro do texto (primeiro { até último })
        match_json = re.search(r'\{.*\}', texto, re.DOTALL)
        if match_json:
            return json.loads(match_json.group())  # Se falhar aqui, é erro real
        raise  # Não encontrou nenhum JSON

def decodificar_json(resposta: str) -> bool:
    """Tenta formatar a string de resposta como JSON visual no Streamlit.
    Retorna True se conseguiu, False se não."""
    try:
        resultado = extrair_json(resposta)
        st.json(resultado)
        return True
    except (json.JSONDecodeError, Exception):
        st.warning("⚠️ Resposta não é um JSON válido")
        st.code(resposta, language="text")
        return False