import random
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from PIL import Image

def get_drive_service():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        erro = str(e).lower()
        print(f"[ERRO DRIVE] Falha na autenticação: {e}")
        if "invalid_grant" in erro or "unauthorized" in erro:
            st.error("Erro de Autenticação Google: Credenciais inválidas ou expiradas.")
        elif "service_account" in erro:
             st.error("Erro de Configuração: Problema no arquivo de serviço (.toml).")
        else:
            st.error("Falha ao conectar no Google Drive.")
        return None

def listar_arquivos(service, folder_id):
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType)",
            pageSize=1000
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"[LOG] Erro ao listar arquivos: {e}")
        return []

def baixar_imagem_drive(service, file_id):
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
    service = get_drive_service()
    if not service: return None

    try:
        root_id = st.secrets["geral"]["DRIVE_FOLDER_ID"]
    except KeyError:
        print(f"[LOG] Configuração ausente: 'DRIVE_FOLDER_ID' não encontrado no secrets.toml")
        st.error("Configuração ausente: 'DRIVE_FOLDER_ID' não encontrado no secrets.toml")
        return None

    # Listar pastas de espécies
    itens_raiz = listar_arquivos(service, root_id)
    if not itens_raiz:
        print(f"[LOG] A pasta raiz do Drive está vazia ou inacessível. ID: {root_id}")
        st.error("A pasta raiz do Drive está vazia ou inacessível.")
        return None

    pastas = [i for i in itens_raiz if i['mimeType'] == 'application/vnd.google-apps.folder']

    if not pastas:
        print(f"[LOG] Erro de Dados: Não existem subpastas (espécies) na raiz {root_id}.")
        st.error("Erro de Dados: Não existem subpastas (espécies).")
        return None

    # Sorteio: Espécie
    pasta_sorteada = random.choice(pastas)
    nome_especie = pasta_sorteada['name']
    id_pasta = pasta_sorteada['id']

    # Sorteio: Imagem
    conteudo_pasta = listar_arquivos(service, id_pasta)
    imagens_validas = [i for i in conteudo_pasta if 'image' in i['mimeType']]

    if not imagens_validas:
        print(f"[LOG] Sorteio Inválido: A espécie '{nome_especie}' foi sorteada, mas a pasta dela está vazia.")
        st.error(f"Sorteio Inválido: A espécie '{nome_especie}' foi sorteada, mas a pasta dela está vazia.")
        return None

    imagem_sorteada = random.choice(imagens_validas)
    print(f"Sorteio Hierárquico: {nome_especie} -> {imagem_sorteada['name']}")

    try:
        img_pil = baixar_imagem_drive(service, imagem_sorteada['id'])
        return img_pil, imagem_sorteada['name'], nome_especie, imagem_sorteada['id']
    except Exception as e:
        erro = str(e).lower()
        print(f"[ERRO DOWNLOAD] {e}")
        
        if "not found" in erro or "404" in erro:
            st.error(f"Imagem não encontrada no Drive (ID: {imagem_sorteada.get('id', '?')})")
        elif "quota" in erro or "limit" in erro or "403" in erro:
             st.error("Cota do Google Drive excedida temporariamente.")
        elif "timeout" in erro:
             st.error("Tempo limite esgotado ao baixar imagem.")
        else:
             st.error("Erro ao baixar a imagem. Detalhes no terminal.")
        return None