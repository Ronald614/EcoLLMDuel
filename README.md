# EcoLLMDuel
Sistema de Avaliação de llms para imagens de armadilhas fotográficas com duelos
### Como Rodar o Projeto EcoLLMDuel

## (1) Criar um ambiente virtual:

``python3 -m venv env``

## (2) Ativar o ambiente virtual

``source env/bin/activate``

## (3) Baixar as dependencias

``pip install -r requirements.txt``

## (4) Adicionar a pasta 'mamiraua' ao diretorio do projeto

> [!IMPORTANT]
> **Aviso sobre as Chaves de API**
>
> Para o correto funcionamento da aplicação, você **deve** definir as seguintes variáveis de ambiente no seu terminal antes de executar o Streamlit:
> ```bash
> export key_api_gpt="sk-sua-chave-openai-aqui"
> export key_api_gemini="AIza-sua-chave-google-aqui"
> ```
> **Lembre-se:** Este passo é temporário e precisa ser refeito a cada nova sessão do terminal.

## (5) Rodar o comando do streamlit

``streamlit run streamlit_app.py``


> [!WARNING]
> Para que a funcionalidade de "Sortear Imagem Aleatória" funcione, é **essencial** criar a pasta `mamiraua/` no diretório principal do projeto. Dentro dela, crie subpastas com os nomes das espécies para organizar as imagens.
