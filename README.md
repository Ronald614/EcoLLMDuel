# EcoLLMDuel
Sistema de Avaliação de llms para imagens de armadilhas fotográficas com duelos
### Como Rodar o Projeto EcoLLMDuel

## (1) Criar um ambiente virtual:

``python3 -m venv env``

## (2) Ativar o ambiente virtual

``source env/bin/activate``

## (3) Baixar as dependencias

``pip install -r requirements.txt``

##(3.1) Adicionar a pasta 'mamiraua' ao diretorio do projeto

## (4) Rodar o comando do streamlit

``streamlit run streamlit_app.py``


> [!WARNING]
> Para que a funcionalidade de "Sortear Imagem Aleatória" funcione, é **essencial** criar a pasta `mamiraua/` no diretório principal do projeto. Dentro dela, crie subpastas com os nomes das espécies para organizar as imagens.
