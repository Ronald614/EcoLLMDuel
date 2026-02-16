# --- CONSTANTES ---
from ai.prompt import PROMPT_TEMPLATE
TEMPERATURA_FIXA = 0.0
LIMITE_TOKENS = 16384

# --- CSS ---
CSS_STYLES = """
<style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {text-align: center;}
    
    /* Texto maior em todo o app (sem forçar cor) */
    .stMarkdown, .stText, .stCaption, p, span, label, li {
        font-size: 1.1rem !important;
    }
    
    /* JSON e código com texto maior */
    .stJson, pre, code { font-size: 1.05rem !important; }
    
    /* Radio buttons e labels */
    .stRadio label, .stTextArea label { 
        font-size: 1.15rem !important; 
    }
    
    /* Textarea desabilitado respeita tema */
    textarea:disabled { -webkit-text-fill-color: inherit !important; opacity: 1 !important; }
    
    .profile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px; border-radius: 10px;
        text-align: center; color: white !important; margin-bottom: 20px;
    }
    .profile-card * { color: white !important; }
    .stButton > button {width: 100%; border-radius: 8px; font-size: 1.1rem !important;}
</style>
"""