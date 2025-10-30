import streamlit as st
from openai import OpenAI 
from PIL import Image 
import base64 
from io import BytesIO
import google.generativeai as genai
import json
import os
import random
import csv
from datetime import datetime
from sqlalchemy import text #para conectar ao banco de dados
import time

# --- CONSTANTES ---
PROMPT_TEMPLATE = """Você é um biólogo especialista em vida selvagem e reconhecimento de imagem. Analise esta imagem de armadilha fotográfica.
Descreva a imagem detalhadamente, identificando qualquer animal presente, incluindo nome científico, nome comum e o número de indivíduos.
Considere as seguintes espécies como possíveis candidatas: {species_str}, mas não se limite apenas a elas.

Retorne a análise em formato JSON com os seguintes campos:
- "Deteccao": "Sim" se animais forem detectados, se não "Nenhuma".
- "Nome Cientifico": O nome científico da espécie.
- "Nome Comum": O nome comum da espécie.
- "Numero de Individuos": A contagem de animais detectados.
- "Descricao da Imagem": Uma descrição detalhada do que é visível na imagem.

Se nenhum animal for detectado, retorne um JSON onde todos os campos são "Nenhum", exceto a "Descricao da Imagem".
"""

# Criar a conexão com o supabase (o Streamlit gerencia isso)
#########################################################333333
conn = st.connection(
    "evaluations_db", 
    type="sql",
    url=st.secrets["DATABASE_URL"]
)
######################################333

# Funcoes para converter as imagens para base64 e para gerar a saida das llms em json e salvar no cvs
# Entrada -> Processamento -> Saida dos dados
# -------------------------------
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
        
def save_evaluation_to_db(evaluation_data):
    """Insere os dados da avaliação no banco de dados SQLite."""
    try:
        query = """
        INSERT INTO evaluations (
            timestamp, image_name, model_a, model_b, 
            evaluation, comments, prompt, temperature
        ) VALUES (
            :timestamp, :image_name, :model_a, :model_b, 
            :evaluation, :comments, :prompt, :temperature
        );
        """
        # A conexão 'conn' já foi criada fora da função
        with conn.session as s:
            s.execute(query, params=evaluation_data)
            s.commit()
    except Exception as e:
        st.error(f"Erro ao salvar no banco de dados: {e}")
#----------------------------------------------


#Funcoes para selecionar a especie
#------------------------------
def load_species_from_file(filename="species.txt"):
    #Load a list of especies from file species.txt
    try:
        with open(filename, "r") as f:
            species = [line.strip() for line in f if line.strip()]
        return species
    except FileNotFoundError:
        # Standart list if dont have archive
        return ["Crax globulosa", "Didelphis albiventris", "Leopardus wiedii", "Panthera onca"]
    
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
#---------------------------------


#Lógica das requests
#-------------------------------
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
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt_text}, 
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"}}]
                }],
        temperature=temp,   
        max_tokens=1024,
    )
    return response.choices[0].message.content


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
            response_text = get_deepseek_response(st.session_state.deepseek_api_key, model_name, prompt, encoded_image, temp)
            decode_json(response_text)
        else:
            error_msg = f"Chave de API não encontrada para o modelo {model_name}."
            st.error(error_msg) # Mostra o erro imediatamente
            return False, error_msg # Retorna a falha e a mensagem
    
        return True, None # <-- Retorna Sucesso e Nenhuma mensagem de erro
    
    except Exception as e:
        error_msg = f"Erro ao chamar o modelo {model_name}: {e}"
        st.error(error_msg) # Mostra o erro imediatamente
        return False, str(error_msg) # Retorna a falha e a exceção
    
#-------------------------------


# Função para sempre iniciar a sessao do usuario e os dados que são persistentes
#---------------------------------
def initialize_state():
    """Centraliza toda a inicialização do session_state."""
    
    # Define os padrões para cada chave
    defaults = {
    # --- Chaves de API ---
    "openai_api_key": st.secrets["OPENAI_API_KEY"],         # Chave da API da OpenAI (lida do SECRET)
    "gemini_api_key": st.secrets["GOOGLE_API_KEY"],          # Chave da API do Google Gemini (lida do SECRET)
    "deepseek_api_key": st.secrets["DEEPSEEK_API_KEY"],      # Chave da API do DeepSeek (lida do SECRET)

    # --- Configuração dos Modelos ---
    "available_models": {                                   # Mapeamento de modelos disponíveis para seus tipos (ex: 2=Gemini)
        #"gpt-4o": 1, "gpt-4o-mini": 1, "gpt-4-turbo": 1,
        "gemini-2.0-flash": 2, "gemini-2.5-flash-image-preview": 2,
        "gemini-2.5-flash-lite-preview-09-2025": 2,
        "gemini-2.0-flash-thinking-exp-01-21": 2,
    },

    # --- Estado do Duelo Atual ---
    "model_a": None,                                        # Nome do modelo sorteado para a Posição A
    "model_b": None,                                        # Nome do modelo sorteado para a Posição B
    "image": None,                                          # Objeto da imagem (PIL.Image) em análise
    "name_image": None,                                     # Nome do arquivo da imagem (para o CSV)
    "species_list": load_species_from_file(),               # Lista de espécies carregada do 'species.txt'

    # --- Flags de Controle de Estado (Controle do Fluxo) ---
    "analysis_run": False,                                  # Flag (True/False): Se a análise já foi executada
    "evaluation_submitted": False,                          # Flag (True/False): Se o formulário de avaliação já foi enviado
    "analysis_succeeded": False,                            # Flag (True/False): Se AMBOS os modelos rodaram com sucesso
    "error_a": None,                                        # Armazena a mensagem de erro do Modelo A (se houver)
    "error_b": None                                         # Armazena a mensagem de erro do Modelo B (se houver)
}
    
    # Itera e define no session_state apenas se a chave não existir
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
#------------------------


#Definindo as colunas e a sidebar
#--------------------------------------
#Funcao para definir a side bar (selecao dos modelos)
def render_sidebar():
    # Sidebar configuration
    with st.sidebar:
        # Information about the connection of the APIs, during use to identify errors (debug)
        st.sidebar.info(f"Key 1 Carregada: {'✅ Sim' if st.session_state.openai_api_key else '❌ Não'}")
        st.sidebar.info(f"Key 2 Carregada: {'✅ Sim' if st.session_state.gemini_api_key else '❌ Não'}")
        st.sidebar.info(f"Key 3 Carregada: {'✅ Sim' if st.session_state.deepseek_api_key else '❌ Não'}")
    
        st.title("Configurações")
    
        if st.toggle("Adicionar Chaves ?"):
            user_key_gpt = st.text_input("Chave para a OpenAi(GPT)", help="Copie e Cole a chave neste campo", type="password")
        
            user_key_gemini = st.text_input("Chave para o Gemini", help="Copie e Cole a chave neste campo",  type="password")
        
            if st.button("Confirmar chaves"):
                st.session_state.openai_api_key = user_key_gpt
                st.session_state.gemini_api_key = user_key_gemini

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
        return temperature, keywords

#Funcao para definir a coluna de entrada das imagens (selecao das imagens)
def image_input_collum(col):
    with col:
        st.header("Imagem de Entrada")
        
        # Opções para obter a imagem
        img_file_buffer = st.file_uploader('Faça upload de uma imagem (PNG, JPG)', type=['png','jpg','jpeg'],)

        if st.button("Usar Imagem Aleatória"):
            img_data = get_random_image("./mamiraua")
            if img_data:
                st.session_state.image, st.session_state.image_name = img_data
                st.session_state.analysis_run = False
                st.session_state.evaluation_submitted = False # Reseta avaliação
        
        if img_file_buffer:
            st.session_state.image = Image.open(img_file_buffer)
            st.session_state.image_name = img_file_buffer.name 
            st.session_state.analysis_run = False
            st.session_state.evaluation_submitted = False # Reseta avaliação
        
        if st.session_state.image:
            # Rezise image for display
            display_image = st.session_state.image.copy()
            display_image.thumbnail((640, 640), Image.Resampling.LANCZOS)
            st.image(display_image, width='stretch') # Alterado para use_column_width

def render_evaluation_form(prompt_usado, temperature_usado):
    """Renderiza a seção de avaliação após a análise."""
    st.markdown("---")
    
    if st.session_state.evaluation_submitted:
        st.success("✅ Avaliação salva com sucesso! Obrigado pelo feedback.")
        st.info(f"""Para sua referência:
        - **Modelo A** era: `{st.session_state.model_a}`
        - **Modelo B** era: `{st.session_state.model_b}`""")
        return # Não mostra o formulário se já foi enviado

    # Se a avaliação ainda não foi enviada, mostra o formulário.
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
                current_evaluation = {
                    "timestamp": datetime.now().isoformat(),
                    "image_name": st.session_state.get("name_image"),
                    "model_a": st.session_state.model_a,
                    "model_b": st.session_state.model_b,
                    "evaluation": evaluation,
                    "comments": comments,
                    "prompt": prompt_usado, # Salva o prompt usado
                    "temperature": temperature_usado
                }
                
                save_evaluation_to_db(current_evaluation)
                st.session_state.evaluation_submitted = True
                st.rerun()
#--------------------


# --- FLUXO DE EXECUÇÃO PRINCIPAL ---
def main():
    
    st.set_page_config(layout="wide")
    st.logo("logo.png")
    st.title("LLM Duel: Análise de Imagens de Armadilha Fotográfica")

    # 1. Inicializa o estado (DEVE ser a primeira chamada do streamlit)
    initialize_state()

    # --- TESTE DE CONEXÃO DO BANCO ---
    try:
        # A conexão é definida na linha 31 (nível global)
        # Vamos tentar usar a conexão 'conn' para fazer uma consulta simples
        with conn.session as s:
           s.execute(text("SELECT 1")) # <-- MUDANÇA AQUI
        
        st.success("✅ Conexão com o Supabase OK!")
    except Exception as e:
        st.error(f"❌ Falha na conexão com o Supabase: {e}")
        st.stop() # Para a execução se o banco falhar
    # --- FIM DO TESTE ---

    # 2. Renderiza a UI e obtém parâmetros dinâmicos
    temperature, keywords = render_sidebar()
    col1, col2, col3 = st.columns([1, 2, 2], gap="medium")
    
    # Passa a 'col1' para a função de renderização
    image_input_collum(col1)

    # 3. Constrói o prompt dinâmico (AGORA é seguro usar o session_state)
    species_str = ", ".join(st.session_state.species_list)
    prompt = PROMPT_TEMPLATE.format(species_str=species_str)

    # 4. Lógica de Análise (O Duelo)
    # Só mostra o botão de análise se tivermos tudo pronto
    if st.session_state.image and st.session_state.model_a and st.session_state.model_b:
        
        # Codifica a imagem uma única vez
        encoded_image = encode_image(st.session_state.image)
        
        if st.button("Analisar Imagem", use_container_width=True):
            # Define as flags de estado
            st.session_state.analysis_run = True
            st.session_state.evaluation_submitted = False
            
            # Limpa erros antigos do estado
            st.session_state.error_a = None
            st.session_state.error_b = None
            
            # Roda a análise para o Modelo A
            sucesso_a = False
            with col2:    
                st.header("Modelo A")
                with st.spinner("Modelo A está analisando..."):
                    sucesso_a, error_a = run_analysis(
                        st.session_state.model_a, 
                        prompt, 
                        st.session_state.image, 
                        encoded_image, 
                        temperature
                    )

            # Roda a análise para o Modelo B
            sucesso_b = False
            with col3:
                st.header("Modelo B")
                with st.spinner("Modelo B está analisando..."):
                    sucesso_b, error_b= run_analysis(
                        st.session_state.model_b, 
                        prompt, 
                        st.session_state.image, 
                        encoded_image, 
                        temperature
                    )
            
            #Armazenar se a analise foi um sucesso no geral
            st.session_state.analysis_succeeded = sucesso_a and sucesso_b
            
            # Salva os erros no session_state para sobreviver ao rerun
            if not sucesso_a:
                st.session_state.error_a = error_a
            if not sucesso_b:
                st.session_state.error_b = error_b
            
            # Força o rerun para o formulário aparecer abaixo
            st.rerun()

    # 5. Lógica de Avaliação (Formulário)
    # Se a análise já rodou, mostra o formulário de avaliação
    if st.session_state.get("analysis_run", False):
        if st.session_state.get("analysis_succeeded", False): # Se os dois modelos nao geraram erros
                render_evaluation_form(prompt, temperature)
        else: 
            # Informar o erro ao usuário e pedir pra reiniciar a analise
            st.error("❌ A análise falhou para um ou ambos os modelos.")
            st.warning("Não é possível registrar uma avaliação para esta execução. Por favor, tente analisar novamente ou use outra imagem.")

            # Lê os erros salvos no session_state e os exibe
            if st.session_state.get("error_a"):
                st.error(f"Erro Modelo A ({st.session_state.model_a}): {st.session_state.error_a}")
            if st.session_state.get("error_b"):
                st.error(f"Erro Modelo B ({st.session_state.model_b}): {st.session_state.error_b}")

# --- PONTO DE ENTRADA DO SCRIPT ---
if __name__ == "__main__":
    main()