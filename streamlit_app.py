from openai import OpenAI 
import streamlit as st 
from PIL import Image 
import base64
from io import BytesIO
import google.generativeai as genai
import json
import os
import random
import csv
from datetime import datetime
import time

# Function to encode the image
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def decode_json(response):
    # Try to parse the response as JSON and display it nicely
    try:
        # Clean the response text to ensure it's valid JSON
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        json_data = json.loads(json_str)
        st.json(json_data)
        
    except json.JSONDecodeError:
        # If JSON parsing fails, show the raw response
        st.write("Raw response (not valid JSON):")
        st.write(response)

def load_species_from_file(filename="species.txt"):
    #Load a list of especies from file species.txt
    try:
        with open(filename, "r") as f:
            species = [line.strip() for line in f if line.strip()]
        return species
    except FileNotFoundError:
        # Standart list if dont have archive
        return ["Crax globulosa", "Didelphis albiventris", "Leopardus wiedii", "Panthera onca"]
    

#----------------------------
#Lógica de sorteio e caminho da imagem
def get_random_image(base_folder="mamiraua"):
    """Seleciona uma imagem aleatória de qualquer subpasta de espécie."""
    
    if not os.path.isdir(base_folder):
        st.sidebar.error(f"Diretório base '{base_folder}' não encontrado.")
        return None
    
    # Lista todas as subpastas disponíveis.
    species_folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]
    if not species_folders:
        st.sidebar.error("Nenhuma pasta de espécie encontrada.")
        return None
    
    # Sorteia uma pasta da lista completa.
    random_species_folder = random.choice(species_folders)
    full_path = os.path.join(base_folder, random_species_folder)

    # Lista as imagens na pasta sorteada.
    images = [img for img in os.listdir(full_path) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not images:
        st.sidebar.error(f"Nenhuma imagem encontrada em '{random_species_folder}'.")
        return None

    # Sorteia uma imagem e a retorna junto com o caminho dela.
    random_image_name = random.choice(images)
    image_path = os.path.join(full_path, random_image_name)
    
    st.sidebar.success(f"Imagem sorteada: {random_species_folder}/{random_image_name}")
    return Image.open(image_path), image_path


#-----------------------------
#Lógica das requests
def get_openai_response(api_key, model_name, prompt_text, encoded_img, temp):
    #Get response of openai api
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"}}
            ]}
        ],
        temperature=temp,
        max_tokens=1024,
    )
    return response.choices[0].message.content

def get_gemini_response(api_key, model_name, prompt_text, img, temp):
    #Get response of gemini api

    genai.configure(api_key=api_key)
    generation_config = genai.types.GenerationConfig(temperature=temp)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content([prompt_text, img], generation_config=generation_config)
    return response.text

def get_deepseek_response(api_key, model_name, prompt_text, encoded_img, temp):
    """Obtém a resposta da API da DeepSeek."""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt_text}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"}}]}],
        temperature=temp,
        max_tokens=1024,
    )
    return response.choices[0].message.content

#Encapsular a lógica do comando da chamada a api
# Crie esta nova função junto com as outras
def run_analysis(model_name, prompt, image, encoded_image, temp):
    try:
        model_type = st.session_state.available_models[model_name]
        
        if model_type == 1 and st.session_state.openai_api_key:
            response_text = get_openai_response(st.session_state.openai_api_key, model_name, prompt, encoded_image, temp)
            decode_json(response_text)
        elif model_type == 2 and st.session_state.gemini_api_key:
            response_text = get_gemini_response(st.session_state.gemini_api_key, model_name, prompt, image, temp)
            decode_json(response_text)
        elif model_type == 3 and st.session_state.deepseek_api_key:
            response_text = get_openai_response(st.session_state.deepseek_api_key, model_name, prompt, encoded_image, temp)
            decode_json(response_text)
        else:
            st.error(f"Chave de API não encontrada para o modelo {model_name}.")
            
    except Exception as e:
        st.error(f"Erro ao chamar o modelo {model_name}: {e}")


#------------------------
#Lógica da Sessao do Usuário
st.set_page_config(layout="wide")

st.logo("logo.png")
# Set page config for full width
st.title("LLM Duel: Análise de Imagens de Armadilha Fotográfica")

# Initialize session state for API keys if not exists
if "openai_api_key" not in st.session_state: st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY") 
if "gemini_api_key" not in st.session_state: st.session_state.gemini_api_key =  os.getenv("GOOGLE_API_KEY")
if "deepseek_api_key" not in st.session_state: st.session_state.deepseek_api_key =  os.getenv("DEEPSEEK_API_KEY")
    
# list of models
if "available_models" not in st.session_state:
    st.session_state.available_models = {
        #OpenAI
        #"gpt-4o":1, 
        #"gpt-4o-mini":1, 
        #"gpt-4-turbo":1, 
        #Gemini
        #"gemini-2.0-flash":2,
        #"gemini-2.5-flash-image-preview":2, 
        #"gemini-2.5-flash-lite-preview-09-2025":2, 
        #"gemini-2.0-flash-thinking-exp-01-21":2,
        #DeepSeek
        "deepseek-chat":3,
        "deepseek-deepseek-reasoner":3,
        }
    
if "model_a" not in st.session_state: st.session_state.model_a = None

if "model_b" not in st.session_state: st.session_state.model_b = None

if "image" not in st.session_state: st.session_state.image = None

if "species_list" not in st.session_state: st.session_state.species_list = load_species_from_file()

if "name_image" not in st.session_state: st.session_state.name_image = None


#Flag para sinalizar quando mostrar o formulario
if "analysis_run" not in st.session_state: st.session_state.analysis_run = False


#-------------------------------
#Lógica dos menus do usuário

# Sidebar configuration
with st.sidebar:
    # Information about the connection of the APIs, during use to identify errors (debug)
    st.sidebar.info(f"Key 1 Carregada: {'✅ Sim' if st.session_state.openai_api_key else '❌ Não'}")
    st.sidebar.info(f"Key 2 Carregada: {'✅ Sim' if st.session_state.gemini_api_key else '❌ Não'}")
    st.sidebar.info(f"Key 3 Carregada: {'✅ Sim' if st.session_state.deepseek_api_key else '❌ Não'}")
    
    st.title("Confirações")
    
    #Random Select model
    if st.button("Sortear os modelos"):
        models = list(st.session_state.available_models)
        sorted_models = random.sample(models, 2)
        st.session_state.model_a = sorted_models[0]
        st.session_state.model_b = sorted_models[1]
        st.session_state.analysis_run = False

    # Temperature slider
    temperature = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="Controla a aleatoriedade. Valores baixos são mais determinísticos"
    )

    # Keywords for image analysis
    keywords = st.multiselect(
        "Selecionar as especies que voce quer focar",
        st.session_state.species_list,
        default=st.session_state.species_list,
        help="Selecione as especies para guiar a análise"
    )

    # Species list management
    new_species = st.text_input(
        "Adicione novas especies a lista de espécies.",
        help="Entre com o nome da especie e aperte Enter para adiciona a lista.",
    )
    
    if new_species and new_species not in st.session_state.species_list:
        st.session_state.species_list.append(new_species)
        st.success(f"Adicionado {new_species} a lista de especies")
        st.rerun()


species_str = ", ".join(st.session_state.species_list)

prompt = f"""Você é um biólogo especialista em vida selvagem e reconhecimento de imagem. Analise esta imagem de armadilha fotográfica.
Descreva a imagem detalhadamente, identificando qualquer animal presente, incluindo nome científico, nome comum e o número de indivíduos.
Considere as seguintes espécies como possíveis candidatas: {species_str}, mas não se limite apenas a elas.

Retorne a análise em formato JSON com os seguintes campos:
- "Deteccao": "Sim" se animais forem detectados, senão "Nenhum".
- "Nome Cientifico": O nome científico da espécie.
- "Nome Comum": O nome comum da espécie.
- "Numero de Individuos": A contagem de animais detectados.
- "Descricao da Imagem": Uma descrição detalhada do que é visível na imagem.

Se nenhum animal for detectado, retorne um JSON onde todos os campos são "Nenhum", exceto a "Descricao da Imagem".
"""

# Layout em três colunas
col1, col2, col3 = st.columns([1, 2, 2], gap="medium")

with col1:
    st.header("Imagem de Entrada")
    
    # Opções para obter a imagem
    img_file_buffer = st.file_uploader(
        'Faça upload de uma imagem (PNG, JPG)', type=['png','jpg','jpeg']
    )
    if st.button("Usar Imagem Aleatória"):
        st.session_state.image, st.session_state.name_image = get_random_image("./mamiraua") 
        st.session_state.analysis_run = False   
    
    if img_file_buffer:
        st.session_state.image = Image.open(img_file_buffer)
        st.session_state.image_name = img_file_buffer.name 
        st.session_state.analysis_run = False
    
    if st.session_state.image:
        # Rezise image for display
        display_image = st.session_state.image.copy()
        display_image.thumbnail((640, 640), Image.Resampling.LANCZOS)
        st.image(display_image, width='stretch')


# Central button for start analise
if st.session_state.image and st.session_state.model_a and st.session_state.model_b:
    if st.button("Analisar Imagem", width='stretch', type="primary", disabled=st.session_state.analysis_run):

        st.session_state.evaluation_submitted = False
        st.session_state.analysis_run = True

        encoded_image = encode_image(st.session_state.image)
        
        # --- Analise in Model A ---
        with col2:
            #st.header(f"Modelo A: {st.session_state.model_a}")
            with st.spinner("Analisando..."):
               run_analysis(st.session_state.model_a, prompt, st.session_state.image, encoded_image, temperature)
        # --- Analise in Model B ---
        with col3:
            #st.header(f"Modelo B: {st.session_state.model_b}")
            with st.spinner("Analisando..."):
               run_analysis(st.session_state.model_b, prompt, st.session_state.image, encoded_image, temperature)
        


#----------------------------------
#Lógica do formulario

## --------------------------------------------------------------------------
# FORMULÁRIO DE AVALIAÇÃO
# --------------------------------------------------------------------------

# Esta função organiza os dados e salva no CSV.
def save_evaluation_to_csv(evaluation_data):
    """Anexa os dados da avaliação a um arquivo CSV."""
    results_file = "evaluation_results.csv"
    
    # Prepara os cabeçalhos do CSV
    fieldnames = [
        "timestamp", "image_name", "model_a", "model_b",
        "evaluation", "comments", "prompt"
    ]
    
    # Garante que o diretório para o arquivo de resultados exista
    os.makedirs(os.path.dirname(results_file) or '.', exist_ok=True)
    
    file_exists = os.path.isfile(results_file)
    
    with open(results_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(evaluation_data)

# A lógica principal da interface começa aqui.
if st.session_state.analysis_run:
    st.markdown("---")
    
    # Se a avaliação já foi enviada, mostra a mensagem de sucesso e revela os modelos.
    if st.session_state.evaluation_submitted:
        st.success("✅ Avaliação salva com sucesso! Obrigado pelo feedback.")
        st.info(f"""Para sua referência:
- **Modelo A** era: `{st.session_state.model_a}`
- **Modelo B** era: `{st.session_state.model_b}`""")
    
    # Se a avaliação ainda não foi enviada, mostra o formulário.
    else:
        with st.form("evaluation_form", clear_on_submit=True):
            st.header("Qual modelo foi melhor?")
            
            evaluation = st.radio(
                "Selecione sua avaliação:",
                options=[
                    "Modelo A foi superior ✅",
                    "Modelo B foi superior ✅",
                    "Empate ⚖️",
                    "Ambos foram ruins ❌"
                ],
                index=None
            )

            comments = st.text_area("Comentários (opcional):", max_chars=140)
            submitted = st.form_submit_button("Salvar Avaliação")

            if submitted:
                if not evaluation:
                    st.warning("Por favor, selecione uma opção de avaliação.")
                else:
                    # Prepara o dicionário de dados para salvar
                    current_evaluation = {
                        "timestamp": datetime.now().isoformat(),
                        "image_name": st.session_state.get("image_name"),
                        "model_a": st.session_state.model_a,
                        "model_b": st.session_state.model_b,
                        "evaluation": evaluation,
                        "comments": comments,
                        #"prompt": prompt
                    }
                    
                    # Chama a função para salvar os dados
                    save_evaluation_to_csv(current_evaluation)
                    
                    # Ativa a flag para indicar que a avaliação foi enviada
                    st.session_state.evaluation_submitted = True
                    st.rerun()