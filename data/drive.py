import os
import random
import streamlit as st
from PIL import Image

# Extensoes de imagem aceitas para o fallback local
_EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

# Caminho padrao do dataset local (relativo a raiz do projeto)
_CAMINHO_LOCAL_PADRAO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mamiraua")


# =============================================================================
#  Google Drive (modo remoto)
# =============================================================================

def _drive_disponivel() -> bool:
    """Verifica se as credenciais do Google Drive estao configuradas."""
    try:
        _ = st.secrets["gcp_service_account"]
        _ = st.secrets["geral"]["DRIVE_FOLDER_ID"]
        return True
    except (KeyError, FileNotFoundError):
        return False


def get_drive_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        erro = str(e).lower()
        print(f"[ERRO DRIVE] Falha na autenticacao: {e}")
        if "invalid_grant" in erro or "unauthorized" in erro:
            st.error("Erro de Autenticacao Google: Credenciais invalidas ou expiradas.")
        elif "service_account" in erro:
             st.error("Erro de Configuracao: Problema no arquivo de servico (.toml).")
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
    import io
    from googleapiclient.http import MediaIoBaseDownload

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


def _obter_imagem_drive():
    """Sorteia uma imagem aleatoria do Google Drive."""
    service = get_drive_service()
    if not service:
        return None

    try:
        root_id = st.secrets["geral"]["DRIVE_FOLDER_ID"]
    except KeyError:
        print(f"[LOG] Configuracao ausente: 'DRIVE_FOLDER_ID' nao encontrado no secrets.toml")
        st.error("Configuracao ausente: 'DRIVE_FOLDER_ID' nao encontrado no secrets.toml")
        return None

    # Listar pastas de especies
    itens_raiz = listar_arquivos(service, root_id)
    if not itens_raiz:
        print(f"[LOG] A pasta raiz do Drive esta vazia ou inacessivel. ID: {root_id}")
        st.error("A pasta raiz do Drive esta vazia ou inacessivel.")
        return None

    pastas = [i for i in itens_raiz if i['mimeType'] == 'application/vnd.google-apps.folder']

    if not pastas:
        print(f"[LOG] Erro de Dados: Nao existem subpastas (especies) na raiz {root_id}.")
        st.error("Erro de Dados: Nao existem subpastas (especies).")
        return None

    # Sorteio: Especie
    pasta_sorteada = random.choice(pastas)
    nome_especie = pasta_sorteada['name']
    id_pasta = pasta_sorteada['id']

    # Sorteio: Imagem
    conteudo_pasta = listar_arquivos(service, id_pasta)
    imagens_validas = [i for i in conteudo_pasta if 'image' in i['mimeType']]

    if not imagens_validas:
        print(f"[LOG] Sorteio Invalido: A especie '{nome_especie}' foi sorteada, mas a pasta dela esta vazia.")
        st.error(f"Sorteio Invalido: A especie '{nome_especie}' foi sorteada, mas a pasta dela esta vazia.")
        return None

    imagem_sorteada = random.choice(imagens_validas)
    print(f"Sorteio Hierarquico (Drive): {nome_especie} -> {imagem_sorteada['name']}")

    try:
        img_pil = baixar_imagem_drive(service, imagem_sorteada['id'])
        return img_pil, imagem_sorteada['name'], nome_especie, imagem_sorteada['id']
    except Exception as e:
        erro = str(e).lower()
        print(f"[ERRO DOWNLOAD] {e}")
        
        if "not found" in erro or "404" in erro:
            st.error(f"Imagem nao encontrada no Drive (ID: {imagem_sorteada.get('id', '?')})")
        elif "quota" in erro or "limit" in erro or "403" in erro:
             st.error("Cota do Google Drive excedida temporariamente.")
        elif "timeout" in erro:
             st.error("Tempo limite esgotado ao baixar imagem.")
        else:
             st.error("Erro ao baixar a imagem. Detalhes no terminal.")
        return None


# =============================================================================
#  Fallback Local (modo offline / desenvolvimento)
# =============================================================================

def _obter_imagem_local(caminho_base: str = None):
    """Sorteia uma imagem aleatoria do diretorio local de especies.
    
    Estrutura esperada:
        mamiraua/
            Pantheraonca/
                img1.jpg
                img2.jpg
            Leoparduswiedii/
                img3.jpg
    """
    pasta_raiz = caminho_base or _CAMINHO_LOCAL_PADRAO

    if not os.path.isdir(pasta_raiz):
        print(f"[LOG] Fallback local: pasta '{pasta_raiz}' nao encontrada.")
        st.error(
            f"Nenhuma fonte de imagens disponivel. "
            f"Configure o Google Drive nos secrets ou crie a pasta '{os.path.basename(pasta_raiz)}/' "
            f"com subpastas de especies na raiz do projeto."
        )
        return None

    # Listar subpastas (cada subpasta = uma especie)
    subpastas = [
        d for d in os.listdir(pasta_raiz)
        if os.path.isdir(os.path.join(pasta_raiz, d)) and not d.startswith(".")
    ]

    if not subpastas:
        print(f"[LOG] Fallback local: nenhuma subpasta de especie em '{pasta_raiz}'.")
        st.error("Erro de Dados: Nao existem subpastas (especies) no diretorio local.")
        return None

    # Sorteio: Especie
    especie = random.choice(subpastas)
    pasta_especie = os.path.join(pasta_raiz, especie)

    # Sorteio: Imagem
    arquivos = [
        f for f in os.listdir(pasta_especie)
        if os.path.splitext(f)[1].lower() in _EXTENSOES_IMAGEM
    ]

    if not arquivos:
        print(f"[LOG] Fallback local: pasta '{especie}' nao contem imagens validas.")
        st.error(f"Sorteio Invalido: A especie '{especie}' foi sorteada, mas a pasta dela esta vazia.")
        return None

    nome_arquivo = random.choice(arquivos)
    caminho_completo = os.path.join(pasta_especie, nome_arquivo)

    print(f"Sorteio Hierarquico (Local): {especie} -> {nome_arquivo}")

    try:
        img_pil = Image.open(caminho_completo)
        # O ID local usa o caminho relativo como identificador unico
        id_local = os.path.relpath(caminho_completo, pasta_raiz)
        return img_pil, nome_arquivo, especie, id_local
    except Exception as e:
        print(f"[ERRO LOCAL] Falha ao abrir imagem '{caminho_completo}': {e}")
        st.error("Erro ao abrir a imagem local. Verifique se o arquivo nao esta corrompido.")
        return None


# =============================================================================
#  Funcao principal (selecao automatica de fonte)
# =============================================================================

def obter_imagem_aleatoria():
    """Sorteia uma imagem aleatoria.
    
    Prioridade:
      1. Google Drive (se as credenciais estiverem configuradas nos secrets)
      2. Diretorio local 'mamiraua/' (fallback para desenvolvimento offline)
    """
    if _drive_disponivel():
        return _obter_imagem_drive()
    
    print("[LOG] Google Drive nao configurado. Usando fallback local.")
    return _obter_imagem_local()