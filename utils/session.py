import streamlit as st

def init():
    
    if "initialization_complete" not in st.session_state:
        # Detectar modelos
        modelos = {}
        
        # OpenAI (Tipo 1)
        if "OPENAI_API_KEY" in st.secrets:
             modelos["gpt-4o"] = 1
             modelos["gpt-4o-mini"] = 1
             modelos["gpt-4.1"] = 1
             modelos["gpt-4.1-mini"] = 1
             modelos["gpt-4.1-nano"] = 1
             modelos["gpt-5-mini"] = 1
        
        # Google Gemini (Tipo 2)
        # if "GOOGLE_API_KEY" in st.secrets or "GOOGLE_API_KEY_2" in st.secrets:
        #     modelos["gemini-3-flash-preview"] = 2
        #     modelos["gemini-2.5-flash"] = 2
        #     modelos["gemini-2.5-flash-lite"] = 2


        # NVIDIA API (Tipo 4)
        # if "NVIDIA_API_KEY" in st.secrets:
        #     # Meta (Vision)
        #     modelos["meta/llama-3.2-90b-vision-instruct"] = 4
        #     modelos["meta/llama-3.2-11b-vision-instruct"] = 4
        #     modelos["meta/llama-4-maverick-17b-128e-instruct"] = 4
        #     modelos["meta/llama-4-scout-17b-16e-instruct"] = 4
        #     # Mistral (Vision)
        #     modelos["mistralai/mistral-large-3-675b-instruct-2512"] = 4
        #     modelos["mistralai/ministral-14b-instruct-2512"] = 4
        #     modelos["mistralai/mistral-medium-3-instruct"] = 4
        #     # Microsoft (Vision)
        #     modelos["microsoft/phi-4-multimodal-instruct"] = 4
        #     modelos["microsoft/phi-3.5-vision-instruct"] = 4
        #     # Google (Vision via NVIDIA)
        #     modelos["google/gemma-3-27b-it"] = 4
        #     # Kimi (via NVIDIA API)
        #     modelos["moonshotai/kimi-k2.5"] = 4

        # Sem modelos = erro
        if not modelos:
            st.error("❌ Nenhuma chave de API configurada no secrets.toml.")
            st.stop()

        st.session_state.update({
            "usuario_info": {
                "name": None,
                "email": None
            },
            "detalhes_usuario": None,
            "modelos_disponiveis": modelos,

            "duelo_ativo": False,
            "analise_executada": False,
            "avaliacao_enviada": False,
            "imagem": None,
            "id_imagem": None,
            "nome_imagem": None,
            "pasta_especie": None,
            "modelo_a": None,
            "modelo_b": None,
            "resp_a": None,
            "resp_b": None,
            "time_a": 0.0,
            "time_b": 0.0,
            "suc_a": False,
            "suc_b": False,
            "historico_duelos": [],
            "initialization_complete": True
        })