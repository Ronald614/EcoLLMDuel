import os
from openai import OpenAI
import google.generativeai as genai

#GERADO COM IA GEMINI 2.5 PRO

def list_openai_models():
    """Busca e imprime os modelos disponíveis da OpenAI."""
    print("--- Verificando Modelos da OpenAI ---")
    api_key = os.getenv("key_api_gpt")

    if not api_key:
        print("-> Erro: A variável de ambiente OPENAI_API_KEY não foi definida.")
        print("   Use o comando: export OPENAI_API_KEY='sk-...'")
        return

    try:
        client = OpenAI(api_key=api_key)
        models_list = client.models.list()
        
        print("-> Modelos disponíveis para sua chave:")
        for model in sorted(models_list, key=lambda m: m.id):
            print(f"   - {model.id}")
            
    except Exception as e:
        print(f"-> Ocorreu um erro ao buscar os modelos da OpenAI: {e}")

def list_gemini_models():
    """Busca e imprime os modelos disponíveis do Google Gemini."""
    print("\n--- Verificando Modelos do Google Gemini ---")
    api_key = os.getenv("key_api_gemini")

    if not api_key:
        print("-> Erro: A variável de ambiente GOOGLE_API_KEY não foi definida.")
        print("   Use o comando: export GOOGLE_API_KEY='AIza...'")
        return

    try:
        genai.configure(api_key=api_key)
        
        print("-> Modelos que suportam 'generateContent' (texto/imagem):")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"   - {model.name}")

    except Exception as e:
        print(f"-> Ocorreu um erro ao buscar os modelos do Gemini: {e}")


#GERADO COM IA GEMINI 2.5 PRO

if __name__ == "__main__":
    list_openai_models()
    list_gemini_models()