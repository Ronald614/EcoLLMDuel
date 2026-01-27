import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy import text
import io
import time
import random

# Configuração inicial da aplicação
st.set_page_config(
    page_title="EcoLLM Duel",
    page_icon="🌿",
    layout="wide"
)

# Estabelece conexão com banco de dados PostgreSQL (Supabase)
conn = st.connection("postgresql", type="sql")

# Configura API do Google Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Identificador da pasta no Google Drive contendo o dataset de imagens
FOLDER_ID_DRIVE = "COLOQUE_AQUI_O_ID_DA_SUA_PASTA_DO_DRIVE"

# Funções para integração com Google Drive

def conectar_drive():
    """
    Estabelece autenticação com Google Drive API utilizando service account.
    
    Returns:
        Resource object da API do Drive ou None em caso de falha
    """
    if "gcp_service_account" not in st.secrets:
        st.error("Credenciais do Google Drive não encontradas na configuração")
        return None
        
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build('drive', 'v3', credentials=creds)

@st.cache_data(ttl=3600)
def listar_imagens_drive():
    """
    Recupera lista de arquivos de imagem disponíveis na pasta configurada.
    Utiliza cache de 1 hora para reduzir chamadas à API.
    
    Returns:
        Lista de dicionários contendo metadados dos arquivos
    """
    try:
        service = conectar_drive()
        if not service: 
            return []
        
        # Query para filtrar apenas imagens não deletadas
        query = f"'{FOLDER_ID_DRIVE}' in parents and trashed = false and mimeType contains 'image/'"
        
        results = service.files().list(
            q=query, 
            fields="files(id, name, webViewLink)",
            pageSize=1000
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        st.error(f"Erro ao listar arquivos do Drive: {e}")
        return []

def baixar_imagem_bytes(file_id):
    """
    Realiza download de imagem para memória RAM sem persistência em disco.
    
    Args:
        file_id: Identificador único do arquivo no Google Drive
        
    Returns:
        Bytes da imagem ou None em caso de erro
    """
    try:
        service = conectar_drive()
        request = service.files().get_media(fileId=file_id)
        arquivo_ram = io.BytesIO()
        downloader = MediaIoBaseDownload(arquivo_ram, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        arquivo_ram.seek(0)
        return arquivo_ram.read()
    except Exception as e:
        st.error(f"Erro ao baixar imagem: {e}")
        return None

# Funções para processamento com modelos de linguagem

def chamar_gemini(modelo_nome, prompt, imagem_bytes):
    """
    Executa inferência em modelo Gemini com input multimodal (texto + imagem).
    
    Args:
        modelo_nome: String identificando a versão do modelo
        prompt: Texto da instrução para o modelo
        imagem_bytes: Dados binários da imagem
        
    Returns:
        Resposta textual do modelo ou mensagem de erro
    """
    try:
        model = genai.GenerativeModel(modelo_nome)
        
        # Converte bytes para objeto PIL Image
        from PIL import Image
        img = Image.open(io.BytesIO(imagem_bytes))
        
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"Erro na inferência do modelo {modelo_nome}: {str(e)}"

# Funções de persistência e cálculo de ranking

def verificar_perfil(email):
    """
    Verifica existência de usuário no banco de dados.
    
    Args:
        email: Endereço de email do usuário
        
    Returns:
        Dicionário com dados do perfil ou None se não encontrado
    """
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
        return None
    except Exception as e:
        print(f"Erro ao consultar banco de dados: {e}")
        return None

def salvar_voto(modelo_a, modelo_b, vencedor, prompt, resp_a, resp_b, img_id):
    """
    Persiste resultado de avaliação comparativa no banco de dados.
    
    Args:
        modelo_a: Identificador do primeiro modelo
        modelo_b: Identificador do segundo modelo
        vencedor: Modelo vencedor ou 'Empate'
        prompt: Texto da instrução utilizada
        resp_a: Resposta do modelo A
        resp_b: Resposta do modelo B
        img_id: Identificador da imagem avaliada
        
    Returns:
        Boolean indicando sucesso da operação
    """
    try:
        with conn.session as s:
            s.execute(
                text("""
                    INSERT INTO evaluations (
                        model_a, model_b, winner, 
                        prompt_text, response_a, response_b, 
                        image_id, timestamp
                    ) VALUES (
                        :ma, :mb, :win, 
                        :prompt, :ra, :rb, 
                        :img_id, NOW()
                    )
                """),
                {
                    "ma": modelo_a, "mb": modelo_b, "win": vencedor,
                    "prompt": prompt, "ra": resp_a, "rb": resp_b,
                    "img_id": img_id
                }
            )
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar avaliação: {e}")
        return False

def calcular_elo_ranking():
    """
    Calcula ranking Elo baseado no histórico completo de avaliações.
    Implementa sistema Elo padrão com K-factor de 32 e rating inicial de 1200.
    
    Returns:
        DataFrame com modelos ordenados por pontuação Elo
    """
    try:
        df = conn.query("SELECT model_a, model_b, winner FROM evaluations", ttl=0, show_spinner=False)
    except:
        return pd.DataFrame()
        
    if df.empty: 
        return pd.DataFrame()

    elos = {}
    k_factor = 32

    def get_elo(m): 
        return elos.get(m, 1200)

    for _, row in df.iterrows():
        ma, mb, win = row['model_a'], row['model_b'], row['winner']
        ra, rb = get_elo(ma), get_elo(mb)
        
        # Calcula probabilidades esperadas
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        eb = 1 / (1 + 10 ** ((ra - rb) / 400))
        
        # Define resultado real (1 = vitória, 0.5 = empate, 0 = derrota)
        sa = 1 if win == ma else (0.5 if win == 'Empate' else 0)
        sb = 1 if win == mb else (0.5 if win == 'Empate' else 0)
        
        # Atualiza ratings
        elos[ma] = ra + k_factor * (sa - ea)
        elos[mb] = rb + k_factor * (sb - eb)

    ranking = [{"Modelo": m, "Elo Score": int(r)} for m, r in elos.items()]
    return pd.DataFrame(ranking).sort_values("Elo Score", ascending=False).reset_index(drop=True)

# Interface principal da aplicação

def main():
    # Sidebar: Sistema de autenticação
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
        st.title("EcoLLM Duel")
        
        if "usuario" not in st.session_state:
            email_input = st.text_input("Email de Acesso")
            if st.button("Entrar"):
                user = verificar_perfil(email_input)
                if user:
                    st.session_state["usuario"] = user
                    st.success(f"Olá, {user.get('name', 'Pesquisador')}!")
                    st.rerun()
                else:
                    st.error("Acesso não autorizado.")
            st.stop()
        else:
            st.write(f"Usuário: **{st.session_state['usuario']['name']}**")
            if st.button("Sair"):
                del st.session_state["usuario"]
                st.rerun()

    # Navegação por abas
    tab_arena, tab_ranking = st.tabs(["Arena de Batalha", "Ranking Global"])

    # Aba 1: Interface de avaliação comparativa
    with tab_arena:
        st.header("Teste Cego de Visão Computacional")
        
        # Seção de seleção de imagem
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            if st.button("Sortear Imagem do Drive", type="primary"):
                with st.spinner("Carregando dataset..."):
                    lista = listar_imagens_drive()
                    if lista:
                        img_data = random.choice(lista)
                        bytes_img = baixar_imagem_bytes(img_data['id'])
                        
                        if bytes_img:
                            # Armazena dados na sessão
                            st.session_state['duelo_img_bytes'] = bytes_img
                            st.session_state['duelo_img_id'] = img_data['id']
                            st.session_state['duelo_img_nome'] = img_data['name']
                            # Limpa resultados anteriores
                            st.session_state.pop('respostas', None) 
                        else:
                            st.error("Erro ao baixar dados da imagem.")
                    else:
                        st.warning("Pasta do Drive vazia ou identificador incorreto.")

        # Exibe imagem selecionada
        if 'duelo_img_bytes' in st.session_state:
            st.image(st.session_state['duelo_img_bytes'], 
                    caption=st.session_state.get('duelo_img_nome'), 
                    width=500)
            
            # Seção de configuração do prompt
            prompt = st.text_area(
                "O que você quer perguntar sobre a imagem?", 
                "Descreva detalhadamente o que você vê nesta imagem sob uma perspectiva ecológica."
            )
            
            modelos = ["gemini-1.5-flash", "gemini-1.5-pro"]
            
            if st.button("INICIAR DUELO"):
                if len(modelos) < 2:
                    st.error("São necessários pelo menos 2 modelos configurados.")
                else:
                    m1, m2 = random.sample(modelos, 2)
                    
                    with st.spinner("Processando análise das imagens..."):
                        # Executa inferência em ambos os modelos
                        r1 = chamar_gemini(m1, prompt, st.session_state['duelo_img_bytes'])
                        r2 = chamar_gemini(m2, prompt, st.session_state['duelo_img_bytes'])
                        
                        # Armazena respostas de forma anonimizada
                        st.session_state['respostas'] = {
                            "A": {"modelo": m1, "texto": r1},
                            "B": {"modelo": m2, "texto": r2}
                        }

        # Seção de votação (exibida apenas após inferência)
        if 'respostas' in st.session_state:
            resp = st.session_state['respostas']
            
            st.divider()
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Modelo A")
                st.info(resp["A"]["texto"])
                if st.button("Votar no A", use_container_width=True):
                    vencedor = resp["A"]["modelo"]
                    salvar_agora(resp, vencedor, prompt)

            with col_b:
                st.subheader("Modelo B")
                st.info(resp["B"]["texto"])
                if st.button("Votar no B", use_container_width=True):
                    vencedor = resp["B"]["modelo"]
                    salvar_agora(resp, vencedor, prompt)
            
            if st.button("Declarar Empate", use_container_width=True):
                 salvar_agora(resp, "Empate", prompt)

    # Aba 2: Visualização de ranking
    with tab_ranking:
        st.header("Leaderboard (Elo Rating)")
        st.markdown("Sistema Elo com ajuste baseado na força relativa dos oponentes.")
        
        df_ranking = calcular_elo_ranking()
        
        if not df_ranking.empty:
            # Visualização gráfica
            st.bar_chart(df_ranking.set_index("Modelo"), color="#4CAF50")
            # Tabela detalhada
            st.dataframe(
                df_ranking, 
                use_container_width=True,
                column_config={
                    "Elo Score": st.column_config.ProgressColumn(
                        format="%d", 
                        min_value=1000, 
                        max_value=1400
                    )
                }
            )
        else:
            st.info("Dados insuficientes para gerar ranking. Realize avaliações na Arena primeiro.")

def salvar_agora(resp, vencedor, prompt):
    """
    Persiste voto e reinicia interface para próxima avaliação.
    
    Args:
        resp: Dicionário com respostas dos modelos
        vencedor: Identificador do modelo vencedor
        prompt: Texto do prompt utilizado
    """
    ma = resp["A"]["modelo"]
    mb = resp["B"]["modelo"]
    
    with st.spinner("Salvando avaliação..."):
        sucesso = salvar_voto(
            ma, mb, vencedor, prompt, 
            resp["A"]["texto"], resp["B"]["texto"], 
            st.session_state.get('duelo_img_id')
        )
        if sucesso:
            st.toast("Voto registrado com sucesso", icon="✅")
            time.sleep(1.5)
            # Limpa estado para próxima rodada
            del st.session_state['respostas']
            del st.session_state['duelo_img_bytes']
            st.rerun()

if __name__ == "__main__":
    main()
