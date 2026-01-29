import streamlit as st
# IA e Modelos
from openai import OpenAI 
import google.generativeai as genai

# Processamento de Imagem
from PIL import Image 
import base64 
from io import BytesIO
import json
import os
import random
import time 

# Dados e Banco
from datetime import datetime
from sqlalchemy import text 
from typing import Optional, Tuple, Dict, Any

# --- IMPORTAÇÕES PARA O GOOGLE DRIVE ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# -- Importações para ranquear os modelos ---
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="EcoLLMDuel", page_icon="🤖")

# --- CSS ---
st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {text-align: center; color: #333;}
    .profile-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px; border-radius: 10px;
        text-align: center; color: white; margin-bottom: 20px;
    }
    .stButton > button {width: 100%; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
PROMPT_TEMPLATE = """Você é um biólogo especialista em vida selvagem e reconhecimento de imagem. Analise esta imagem de armadilha fotográfica.
Descreva a imagem detalhadamente, identificando qualquer animal presente, incluindo nome científico, nome comum e o número de indivíduos.

Retorne a análise em formato JSON com os seguintes campos:
- "Deteccao": "Sim" se animais forem detectados, se não "Nenhuma".
- "Nome Cientifico": O nome científico da espécie.
- "Nome Comum": O nome comum da espécie.
- "Numero de Individuos": A contagem de animais detectados.
- "Descricao da Imagem": Uma descrição detalhada do que é visível na imagem.

Se nenhum animal for detectado, retorne um JSON onde todos os campos são "Nenhum", exceto a "Descricao da Imagem".
"""
TEMPERATURA_FIXA = 0.7
LIMITE_TOKENS = 4096

# --- CONEXÃO COM BANCO DE DADOS ---
conn = st.connection("evaluations_db", type="sql", url=st.secrets["DATABASE_URL"])

# --- FUNÇÕES AUXILIARES ---
def codificar_imagem(imagem: Image.Image) -> str:
    """Converte imagem PIL para string base64."""
    buffer = BytesIO()
    imagem.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def decodificar_json(resposta: str) -> None:
    """Tenta formatar a string de resposta como JSON visual no Streamlit."""
    try:
        texto = resposta.strip()
        if texto.startswith("```json"): texto = texto[7:]
        if texto.endswith("```"): texto = texto[:-3]
        st.json(json.loads(texto.strip()))
    except json.JSONDecodeError:
        # Mostra o texto cru se não for JSON, mas formatado como código
        st.warning("⚠️ Resposta não é um JSON válido")
        st.code(resposta, language="text")

# --- FUNÇÕES DO GOOGLE DRIVE ---
def get_drive_service():
    """Autentica e retorna o serviço do Drive."""
    try:
        # Carrega as credenciais dos secrets do Streamlit
        creds_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Erro ao conectar no Google Drive: {e}") # Log no terminal
        return None

def listar_arquivos(service, folder_id):
    """Lista arquivos e pastas dentro de um ID."""
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType)",
            pageSize=1000
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"Erro ao listar arquivos: {e}") # Log no terminal
        return []

def baixar_imagem_drive(service, file_id):
    """Baixa o conteúdo da imagem e converte para PIL Image."""
    try:
        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        file_io.seek(0)
        return Image.open(file_io)
    except Exception as e:
        raise e

def obter_imagem_aleatoria():
    """
    Busca uma imagem no Google Drive com Rigor Estatístico.
    Retorna: (ImagemPIL, NomeArquivo, NomeEspecie, IDArquivo)
    """
    service = get_drive_service()
    if not service:
        return None

    try:
        root_id = st.secrets["geral"]["DRIVE_FOLDER_ID"]
    except KeyError:
        st.error("❌ Configuração ausente: 'DRIVE_FOLDER_ID' não encontrado no secrets.toml")
        return None
    
    # 1. Listar pastas na raiz
    itens_raiz = listar_arquivos(service, root_id)
    if not itens_raiz:
        st.error("❌ A pasta raiz do Drive está vazia ou inacessível.")
        return None

    # Filtra apenas pastas
    pastas = [i for i in itens_raiz if i['mimeType'] == 'application/vnd.google-apps.folder']

    if not pastas:
        st.error("❌ Erro de Dados: Não existem subpastas (espécies) na pasta raiz informada.")
        return None

    # --- ETAPA 1: Sorteio da Pasta (Espécie) ---
    pasta_sorteada = random.choice(pastas)
    nome_especie = pasta_sorteada['name']
    id_pasta = pasta_sorteada['id']

    # --- ETAPA 2: Busca conteúdo da pasta sorteada ---
    conteudo_pasta = listar_arquivos(service, id_pasta)
    imagens_validas = [i for i in conteudo_pasta if 'image' in i['mimeType']]

    if not imagens_validas:
        st.error(f"⚠️ Sorteio Inválido: A espécie '{nome_especie}' foi sorteada, mas a pasta dela está vazia.")
        return None

    # --- ETAPA 3: Sorteio da Imagem ---
    imagem_sorteada = random.choice(imagens_validas)
    
    try:
        img_pil = baixar_imagem_drive(service, imagem_sorteada['id'])
        return img_pil, imagem_sorteada['name'], nome_especie, imagem_sorteada['id']
    except Exception as e:
        st.error(f"Erro ao baixar a imagem sorteada ({imagem_sorteada['name']}): {e}")
        return None

# --- FUNÇÕES DE BANCO DE DADOS (PERFIL E AVALIAÇÃO) ---
def verificar_perfil(email):
    email_tratado = email.lower().strip()
    try:
        df = conn.query(
            "SELECT * FROM user_profiles WHERE email = :email", 
            params={"email": email_tratado}, 
            ttl=0,
            show_spinner=False
        )
        if not df.empty:
            return df.iloc[0].to_dict()
        else:
            return None
    except Exception as e:
        return None

def salvar_perfil_novo(dados):
    """Insere um novo usuário na tabela user_profiles."""
    try:
        query = text("""
            INSERT INTO user_profiles (
                email, name, institution, profession, age, gender,
                works_environmental_area, has_forest_management_exp,
                has_animal_monitoring_exp, has_camera_trap_exp
            ) VALUES (
                :email, :name, :institution, :profession, :age, :gender,
                :env_area, :forest_exp, :monitor_exp, :camera_exp
            )
        """)
        with conn.session as s:
            s.execute(query, dados)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar perfil: {e}")
        return False

def salvar_avaliacao(dados: Dict[str, Any]) -> bool:
    """Salva a avaliação completa na tabela evaluations."""
    try:
        query = text("""
            INSERT INTO evaluations (
                evaluator_email, image_path, image_id, species,
                model_a, model_b,
                time_a, time_b, text_len_a, text_len_b,
                model_response_a, model_response_b,
                result_code, comments,
                prompt, temperature
            ) VALUES (
                :email, :img_name, :img_id, :species,
                :mod_a, :mod_b,
                :t_a, :t_b, :len_a, :len_b,
                :resp_a, :resp_b,
                :result, :obs,
                :prmt, :temp
            )
        """)
        
        parametros = {
            "email": dados["evaluator_email"],
            "img_name": dados["image_name"],
            "img_id": dados["image_id"],
            "species": dados["species_folder"],
            "mod_a": dados["model_a"],
            "mod_b": dados["model_b"],
            "t_a": dados["time_a"],
            "t_b": dados["time_b"],
            "len_a": dados["text_len_a"],
            "len_b": dados["text_len_b"],
            "resp_a": dados["model_response_a"],
            "resp_b": dados["model_response_b"],
            "result": dados["result_code"],
            "obs": dados["comments"],
            "prmt": dados["prompt"],
            "temp": dados["temperature"]
        }
        
        with conn.session as s:
            s.execute(query, parametros)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar avaliação: {e}")
        return False


# --- LÓGICA DE IA (VERSÃO REAL - COM RETRY) ---
def executar_analise(nome_modelo, prompt, imagem, img_codificada):
    start = time.time()
    max_retries = 2
    # Tempo de espera progressivo para evitar erro de cota
    tempo_espera = 20 

    for tentativa in range(max_retries):
        try:
            # Identifica qual API usar com base no ID definido no init()
            # 1=OpenAI, 2=Gemini, 3=DeepSeek
            tipo = st.session_state.modelos_disponiveis.get(nome_modelo)
            resp = ""
            
            # --- TIPO 1: OPENAI (GPT-4o, etc) ---
            if tipo == 1: 
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                r = client.chat.completions.create(
                    model=nome_modelo, 
                    messages=[{
                        "role":"user", 
                        "content":[
                            {"type":"text","text":prompt},
                            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                        ]
                    }],
                    temperature=TEMPERATURA_FIXA,
                    max_tokens=LIMITE_TOKENS
                )
                resp = r.choices[0].message.content
                
            # --- TIPO 2: GOOGLE GEMINI ---
            elif tipo == 2: 
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                config = genai.types.GenerationConfig(
                    temperature=TEMPERATURA_FIXA,
                    max_output_tokens=LIMITE_TOKENS
                )
                model = genai.GenerativeModel(nome_modelo)
                # O Gemini aceita a imagem PIL direto, sem base64
                r = model.generate_content(
                    [prompt, imagem], 
                    generation_config=config
                )
                resp = r.text

            # --- TIPO 3: DEEPSEEK ---
            elif tipo == 3: 
                client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com/v1")
                r = client.chat.completions.create(
                    model=nome_modelo, 
                    messages=[{
                        "role":"user", 
                        "content":[
                            {"type":"text","text":prompt},
                            # Nota: DeepSeek Vision precisa ver se suporta URL base64 na versão atual
                            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_codificada}"}}
                        ]
                    }],
                    temperature=TEMPERATURA_FIXA,
                    max_tokens=LIMITE_TOKENS
                )
                resp = r.choices[0].message.content

            # SUCESSO: Retorna True, a resposta real e o tempo gasto
            return True, resp, time.time() - start
        
        except Exception as e:
            erro_msg = str(e)
            
            # --- TRATAMENTO DE ERRO DE COTA (429) ---
            # Se for erro de limite, esperamos e tentamos de novo
            if ("429" in erro_msg or "quota" in erro_msg or "exhausted" in erro_msg) and tentativa < max_retries - 1:
                print(f"⚠️ [LOG] Cota excedida no {nome_modelo}. Tentativa {tentativa+1}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue 
            
            # --- ERRO FATAL ---
            # Se não for cota ou se acabaram as tentativas
            print(f"❌ [LOG] Erro fatal no modelo {nome_modelo}: {erro_msg}")
            return False, None, time.time() - start

    # Se saiu do loop, falhou em todas as tentativas
    print(f"❌ [LOG] Falha total no modelo {nome_modelo} após {max_retries} tentativas.")
    return False, None, time.time() - start


# --- INICIALIZAÇÃO ---
def init():
    if "modelos_disponiveis" not in st.session_state:
        st.session_state.update({
            "modelos_disponiveis": {
                "gemini-2.0-flash": 2, 
                "gemini-2.5-flash": 2,
                # "gpt-4o": 1,
            },
            "detalhes_usuario": None,
            "analise_executada": False,
            "imagem": None,
            "id_imagem": None,
            "nome_imagem": None,
            "pasta_especie": None
        })

# --- UI: BARRA LATERAL ---
def renderizar_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg", width=100)
        
        if st.user.is_logged_in:
            st.markdown(f"""
            <div class="profile-card">
                <h3>{st.user.name}</h3>
                <small>{st.user.email}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.detalhes_usuario:
                st.success("✅ Perfil Carregado")
                
            if st.button("Sair (Logout)", type="secondary"):
                st.logout()
        else:
            st.warning("Usuário não identificado.")

# --- UI: FORMULÁRIO DE CADASTRO ---
def form_cadastro():
    st.info("👋 Olá! Antes de começar, precisamos conhecer seu perfil técnico.")
    
    with st.form("cadastro_completo"):
        c1, c2 = st.columns(2)
        with c1:
            inst = st.text_input("Instituição (Ex: UFAM)")
            prof = st.text_input("Profissão / Curso")
            idade = st.number_input("Idade", min_value=10, max_value=100, step=1)
        with c2:
            genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro", "Prefiro não dizer"])
            st.markdown("**Experiência Técnica:**")
            area_amb = st.checkbox("Trabalha/Estuda na área ambiental?")
            manejo = st.checkbox("Já fez manejo florestal?")
            monitor = st.checkbox("Já trabalhou com monitoramento de animais?")
            camera = st.checkbox("Já trabalhou com armadilhas fotográficas?")

        # CORREÇÃO: use_container_width=True em vez de width='stretch'
        if st.form_submit_button("Salvar e Continuar", use_container_width=True):
            if inst and prof:
                dados_usuario = {
                    "email": st.user.email,
                    "name": st.user.name,
                    "institution": inst,
                    "profession": prof,
                    "age": idade,
                    "gender": genero,
                    "env_area": area_amb,
                    "forest_exp": manejo,
                    "monitor_exp": monitor,
                    "camera_exp": camera
                }
                
                if salvar_perfil_novo(dados_usuario):
                    st.session_state.detalhes_usuario = dados_usuario
                    st.success("Cadastro realizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Por favor, preencha Instituição e Profissão.")



# --- FUNÇÕES DE RANKING (ELO & BRADLEY-TERRY) ---
def carregar_dados_duelos():
    """Busca todos os duelos finalizados no banco."""
    try:
        # Pega apenas as colunas necessárias
        query = "SELECT model_a, model_b, result_code FROM evaluations"
        df = conn.query(query, ttl=0, show_spinner=False)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados para ranking: {e}")
        return pd.DataFrame()

def calcular_elo(df, k_factor=32):
    """
    Calcula o Rating Elo para cada modelo com base no histórico.
    Base inicial = 1000.
    """
    if df.empty:
        return pd.DataFrame()

    # Identifica todos os modelos únicos
    todos_modelos = set(df['model_a'].unique()) | set(df['model_b'].unique())
    ratings = {model: 1000.0 for model in todos_modelos}

    # Itera sobre cada duelo cronologicamente (assumindo ordem de inserção)
    for _, row in df.iterrows():
        r_a = ratings[row['model_a']]
        r_b = ratings[row['model_b']]
        
        # Define o score real (S_a)
        # A>B: A ganha (1.0)
        # A<B: B ganha (0.0)
        # A=B ou !A!B: Empate (0.5)
        if row['result_code'] == 'A>B':
            s_a = 1.0
        elif row['result_code'] == 'A<B':
            s_a = 0.0
        else:
            s_a = 0.5
        
        # Score esperado (E_a)
        e_a = 1 / (1 + 10 ** ((r_b - r_a) / 400))
        
        # Atualiza ratings
        ratings[row['model_a']] = r_a + k_factor * (s_a - e_a)
        ratings[row['model_b']] = r_b + k_factor * ((1 - s_a) - (1 - e_a))

    # Formata para DataFrame
    rank_df = pd.DataFrame(list(ratings.items()), columns=['Modelo', 'Elo Rating'])
    rank_df = rank_df.sort_values(by='Elo Rating', ascending=False).reset_index(drop=True)
    rank_df.index += 1 # Começar do 1
    return rank_df

def calcular_bradley_terry(df, iterações=100):
    """
    Estima a força dos modelos usando o método iterativo de Bradley-Terry.
    """
    if df.empty:
        return pd.DataFrame()

    models = list(set(df['model_a'].unique()) | set(df['model_b'].unique()))
    n_models = len(models)
    model_to_idx = {m: i for i, m in enumerate(models)}
    
    # Matriz de vitórias (wins[i][j] = quantas vezes i ganhou de j)
    wins = np.zeros((n_models, n_models))
    # Matriz de partidas (matches[i][j] = quantas vezes i jogou contra j)
    matches = np.zeros((n_models, n_models))

    for _, row in df.iterrows():
        idx_a = model_to_idx[row['model_a']]
        idx_b = model_to_idx[row['model_b']]
        
        matches[idx_a][idx_b] += 1
        matches[idx_b][idx_a] += 1
        
        if row['result_code'] == 'A>B':
            wins[idx_a][idx_b] += 1
        elif row['result_code'] == 'A<B':
            wins[idx_b][idx_a] += 1
        else:
            # Empates contam como 0.5 vitória para cada
            wins[idx_a][idx_b] += 0.5
            wins[idx_b][idx_a] += 0.5

    # Inicializa pontuações (p) iguais
    p = np.ones(n_models) / n_models
    
    # Algoritmo iterativo (MM algorithm)
    for _ in range(iterações):
        p_new = np.zeros(n_models)
        total_wins = np.sum(wins, axis=1)
        
        for i in range(n_models):
            soma_denominador = 0
            for j in range(n_models):
                if i != j and matches[i][j] > 0:
                    soma_denominador += matches[i][j] / (p[i] + p[j])
            
            if soma_denominador > 0:
                p_new[i] = total_wins[i] / soma_denominador
            else:
                p_new[i] = p[i] # Mantém se não jogou
        
        # Normaliza para soma = 1
        p_new /= np.sum(p_new)
        
        # Verifica convergência (opcional, aqui faremos fixo)
        p = p_new

    # Escala para um valor mais legível (ex: base 1000)
    # Geralmente logaritmo é usado para escala similar a Elo, mas vamos usar probabilidade pura * 1000
    scores = p * 10000 
    
    rank_df = pd.DataFrame({
        'Modelo': models,
        'BT Score': scores
    })
    rank_df = rank_df.sort_values(by='BT Score', ascending=False).reset_index(drop=True)
    rank_df.index += 1
    return rank_df

def main():
    init()
    
    # 1. Login
    if not st.user.is_logged_in:
        st.title("🦁 Duelador de IA")
        st.info("Faça login com Google para acessar a ferramenta.")
        if st.button("🔑 Entrar com Google", type="primary"):
            st.login("google")
        st.stop()
        
    renderizar_sidebar()
    
    # 2. Verificação de Perfil
    if not st.session_state.detalhes_usuario:
        with st.spinner("Verificando cadastro..."):
            perfil_existente = verificar_perfil(st.user.email)
            
        if perfil_existente:
            st.session_state.detalhes_usuario = perfil_existente
            st.rerun()
        else:
            st.title("Completar Perfil")
            form_cadastro()
            st.stop()
        
    st.title("🛡️ EcoLLM Arena")

    # --- CRIAÇÃO DAS ABAS ---
    tab_arena, tab_rank = st.tabs(["⚔️ Arena de Duelo", "🏆 Leaderboard (Rank)"])

    # ===================================================
    # ABA 1: ARENA DE DUELO
    # ===================================================
    with tab_arena:
        st.caption("Compare modelos e ajude a classificar a melhor IA para biologia.")
        
        # --- BOTÃO DE SORTEIO ---
        if st.button("🔄 Sortear Novo Duelo", type="primary"):
            st.session_state.analise_executada = False
            st.session_state.avaliacao_enviada = False
            
            dados_img = obter_imagem_aleatoria()
            
            if dados_img:
                img, nome_arq, especie, id_arq = dados_img
                
                st.session_state.imagem = img
                st.session_state.nome_imagem = nome_arq
                st.session_state.pasta_especie = especie
                st.session_state.id_imagem = id_arq
                
                mods = list(st.session_state.modelos_disponiveis.keys())
                if len(mods) >= 2:
                    st.session_state.modelo_a, st.session_state.modelo_b = random.sample(mods, 2)
                    
                    enc = codificar_imagem(st.session_state.imagem)
                    
                    with st.spinner("Analisando imagens... (Isso pode demorar um pouco)"):
                        # Modelo A
                        sa, ra, ta = executar_analise(st.session_state.modelo_a, PROMPT_TEMPLATE, st.session_state.imagem, enc)
                        time.sleep(1) 
                        # Modelo B
                        sb, rb, tb = executar_analise(st.session_state.modelo_b, PROMPT_TEMPLATE, st.session_state.imagem, enc)
                        
                        st.session_state.update({
                            "resp_a": ra, "time_a": ta, "suc_a": sa,
                            "resp_b": rb, "time_b": tb, "suc_b": sb,
                            "analise_executada": True
                        })
                    st.rerun()
                else:
                    st.error("Não há modelos suficientes configurados (mínimo 2).")
            else:
                pass 

        # --- EXIBIÇÃO DOS RESULTADOS ---
        if st.session_state.get("analise_executada") and st.session_state.get("imagem"):
            sucesso_total = st.session_state.get("suc_a") and st.session_state.get("suc_b")

            if sucesso_total:
                col_img, col_texto = st.columns([0.4, 0.6]) 

                with col_img:
                    st.markdown("#### 📸 Imagem da Armadilha")
                    st.image(
                        st.session_state.imagem, 
                        caption=f"Espécie: {st.session_state.pasta_especie}", 
                        width="stretch"
                    )

                with col_texto:
                    st.markdown("#### 📝 Prompt Enviado")
                    st.text_area(
                        label="Prompt",
                        value=PROMPT_TEMPLATE, 
                        height=300,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                
                st.divider()

                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Modelo A")
                    st.caption(f"Tempo: {st.session_state.time_a:.2f}s")
                    decodificar_json(st.session_state.resp_a)
                with c2:
                    st.subheader("Modelo B")
                    st.caption(f"Tempo: {st.session_state.time_b:.2f}s")
                    decodificar_json(st.session_state.resp_b)
                    
                # --- ÁREA DE VOTAÇÃO ---
                if not st.session_state.avaliacao_enviada:
                    st.divider()
                    st.markdown("### 👨‍⚖️ Qual seu veredito ?")
                    
                    with st.form("voto"):
                        voto = st.radio("Qual modelo descreveu melhor?", 
                                        ["Modelo A", "Modelo B", "Empate", "Ambos Ruins"], 
                                        horizontal=True)
                        
                        obs = st.text_area("Observações (Opcional)")
                        
                        if st.form_submit_button("✅ Confirmar Avaliação", width="stretch"):
                            if voto:
                                mapa = {"Modelo A": "A>B", "Modelo B": "A<B", "Empate": "A=B", "Ambos Ruins": "!A!B"}
                                
                                dados_salvar = {
                                    "evaluator_email": st.user.email,
                                    "image_name": st.session_state.nome_imagem,
                                    "image_id": st.session_state.id_imagem,
                                    "species_folder": st.session_state.pasta_especie,
                                    "model_a": st.session_state.modelo_a, 
                                    "model_b": st.session_state.modelo_b,
                                    "model_response_a": st.session_state.resp_a,
                                    "model_response_b": st.session_state.resp_b,
                                    "result_code": mapa[voto],
                                    "text_len_a": len(st.session_state.resp_a), 
                                    "text_len_b": len(st.session_state.resp_b),
                                    "time_a": st.session_state.time_a, 
                                    "time_b": st.session_state.time_b,
                                    "comments": obs, 
                                    "prompt": PROMPT_TEMPLATE, 
                                    "temperature": TEMPERATURA_FIXA
                                }
                                
                                if salvar_avaliacao(dados_salvar):
                                    st.session_state.avaliacao_enviada = True
                                    st.success("🎉 Avaliação Registrada! Obrigado.")
                                    time.sleep(1.5)
                                    st.rerun()
                            else:
                                st.warning("Selecione uma opção de voto.")

            else:
                st.error("⚠️ Duelo cancelado: Um dos modelos falhou.")
                msg = ""
                if not st.session_state.get("suc_a"): msg += f"- Falha: {st.session_state.modelo_a}\n"
                if not st.session_state.get("suc_b"): msg += f"- Falha: {st.session_state.modelo_b}"
                st.text(msg)

    # ===================================================
    # ABA 2: RANKING (NOVO CÓDIGO)
    # ===================================================
    with tab_rank:
        st.header("🏆 Classificação Global")
        st.markdown("Ranking gerado com base em todas as avaliações salvas no banco de dados.")
        
        if st.button("🔄 Atualizar Ranking"):
            st.rerun()

        # Carregar dados
        df_duelos = carregar_dados_duelos()
        
        if not df_duelos.empty:
            # Stats básicas
            total_batalhas = len(df_duelos)
            total_modelos = len(set(df_duelos['model_a'].unique()) | set(df_duelos['model_b'].unique()))
            
            m1, m2 = st.columns(2)
            m1.metric("Total de Batalhas", total_batalhas)
            m2.metric("Modelos Avaliados", total_modelos)
            
            st.divider()
            
            # --- TABELA ELO ---
            st.subheader("📈 Elo Rating System")
            st.caption("Sistema padrão usado em Xadrez. Começa em 1000.")
            df_elo = calcular_elo(df_duelos)
            
            # Formatação bonita para o Elo
            st.dataframe(
                df_elo, 
                width="stretch",
                column_config={
                    "Elo Rating": st.column_config.NumberColumn(format="%.0f")
                }
            )

            st.divider()

            # --- TABELA BRADLEY-TERRY ---
            st.subheader("📊 Bradley-Terry Model")
            st.caption("Modelo probabilístico estatístico (Score relativo).")
            df_bt = calcular_bradley_terry(df_duelos)
            
            st.dataframe(
                df_bt, 
                width="stretch",
                column_config={
                    "BT Score": st.column_config.ProgressColumn(
                        format="%.2f",
                        min_value=0,
                        max_value=max(df_bt['BT Score']) if not df_bt.empty else 1000
                    )
                }
            )
        else:
            st.info("Nenhum duelo realizado ainda. Vote na aba 'Arena' para gerar dados!")

if __name__ == "__main__":
    main()
