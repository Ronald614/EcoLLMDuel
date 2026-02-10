import streamlit as st

def init():
    """
    Inicializa variáveis de session_state.
    Garante que todas as chaves existam para evitar KeyError.
    """
    
    if "initialization_complete" not in st.session_state:
        # Detectar modelos disponíveis
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
        if "GOOGLE_API_KEY" in st.secrets or "GOOGLE_API_KEY_2" in st.secrets:
            modelos["gemini-2.0-flash"] = 2  # Rápido e gratuito
            modelos["gemini-2.5-flash"] = 2  # Nova geração multimodal
            modelos["gemini-2.5-flash-lite"] = 2 # Versão Lite
            # modelos["gemini-3-flash"] = 2 # (Opcional: se disponível na API)


        # NVIDIA API (Tipo 4)
        if "NVIDIA_API_KEY" in st.secrets:
            # Meta (Vision)
            modelos["meta/llama-3.2-90b-vision-instruct"] = 4
            modelos["meta/llama-3.2-11b-vision-instruct"] = 4
            modelos["meta/llama-4-maverick-17b-128e-instruct"] = 4
            modelos["meta/llama-4-scout-17b-16e-instruct"] = 4
            # Mistral (Vision)
            modelos["mistralai/mistral-large-3-675b-instruct-2512"] = 4
            modelos["mistralai/ministral-14b-instruct-2512"] = 4
            modelos["mistralai/mistral-medium-3-instruct"] = 4
            # Microsoft (Vision)
            modelos["microsoft/phi-4-multimodal-instruct"] = 4
            modelos["microsoft/phi-3.5-vision-instruct"] = 4
            # Google (Vision via NVIDIA)
            modelos["google/gemma-3-27b-it"] = 4
            # Kimi (via NVIDIA API)
            modelos["moonshotai/kimi-k2.5"] = 4

        # Sem modelos = erro fatal
        if not modelos:
            st.error("❌ Nenhuma chave de API configurada no secrets.toml. Adicione pelo menos uma (GOOGLE_API_KEY, NVIDIA_API_KEY, etc).")
            st.stop()

        st.session_state.update({
            # ===== AUTENTICAÇÃO =====
            "usuario_info": {
                "name": None,
                "email": None,
                "is_logged_in": False
            },
            "detalhes_usuario": None,
            
            # ===== CONFIGURAÇÃO DE MODELOS =====
            "modelos_disponiveis": modelos,

            
            # ===== ARENA: FLAGS DE CONTROLE =====
            "duelo_ativo": False,           # Flag: duelo foi iniciado
            "analise_executada": False,     # Flag: análise completa
            "avaliacao_enviada": False,     # Flag: voto registrado
            
            # ===== ARENA: ESTADO DE IMAGEM =====
            "imagem": None,                 # PIL Image
            "id_imagem": None,              # String ID
            "nome_imagem": None,            # String nome arquivo
            "pasta_especie": None,          # String espécie
            
            # ===== ARENA: MODELOS SELECIONADOS =====
            "modelo_a": None,               # String nome modelo A
            "modelo_b": None,               # String nome modelo B
            
            # ===== ARENA: RESPOSTAS DOS MODELOS =====
            "resp_a": None,                 # String resposta modelo A
            "resp_b": None,                 # String resposta modelo B
            "time_a": 0.0,                  # Float latência modelo A (segundos)
            "time_b": 0.0,                  # Float latência modelo B (segundos)
            "suc_a": False,                 # Bool sucesso modelo A
            "suc_b": False,                 # Bool sucesso modelo B
            
            # ===== HISTÓRICO DE DUELOS =====
            "historico_duelos": [],          # Lista dos últimos duelos
            
            # ===== MARKER DE INICIALIZAÇÃO =====
            "initialization_complete": True
        })