# EcoLLMDuel

> **Sistema de Avaliação de Modelos de IA para Análise de Imagens de Armadilhas Fotográficas**

Plataforma de avaliação baseada em duelos de modelos de linguagem e visão computacional para identificação e classificação de fauna silvestre em imagens de armadilhas fotográficas. O sistema integra Streamlit, APIs de visão (OpenAI, Google Gemini, Kimi/Moonshot AI) e algoritmos de consenso e ordenação estatística.

## Índice

- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução e Fluxo de Uso](#execução-e-fluxo-de-uso)
- [Tecnologias](#tecnologias)
- [Desenvolvimento](#desenvolvimento)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Diretrizes de Segurança e Dados](#diretrizes-de-segurança-e-dados)
- [Deploy](#deploy)
- [Resolução de Problemas](#resolução-de-problemas)
- [Contribuições](#contribuições)
- [Licença](#licença)
- [Contato](#contato)
- [Agradecimentos](#agradecimentos)

---

## Funcionalidades

- **Arena de Avaliação**: Comparação pareada cega (*blind evaluation*) de saídas geradas por dois modelos distintos.
- **Integração Multimodal**: Suporte a modelos via OpenAI, Google Gemini e Kimi (Moonshot AI).
- **Sistemas de Ranking**: Cálculo de classificação e ordenação utilizando modelos Elo Rating e Bradley-Terry.
- **Rastreabilidade**: Gerenciamento e histórico de avaliações por perfil de usuário.
- **Tabela de Classificação (*Leaderboard*)**: Atualização em tempo real das métricas de acurácia relativa dos modelos.
- **Saída Estruturada**: Extração padronizada de metadados em JSON (táxon científico, nome comum e contagem de indivíduos).
- **Métricas de Desempenho**: Registro de latência de inferência e resposta por provedor.

---

## Pré-requisitos

- **Python 3.12+**
- **PostgreSQL 12+**
- **Chaves de API válidas**:
  - OpenAI
  - Google Cloud Console (Gemini API)
  - Moonshot AI (Kimi)

---

## Instalação

### 1. Clonagem do Repositório

```bash
git clone [https://github.com/Ronald614/EcoLLMDuel.git](https://github.com/Ronald614/EcoLLMDuel.git)
cd EcoLLMDuel
```

### 2. Criação do Ambiente Virtual

```bash
python3 -m venv env
```

### 3. Ativação do Ambiente Virtual

**Linux / macOS:**
```bash
source env/bin/activate
```

**Windows:**
```bash
.\env\Scripts\activate
```

### 4. Instalação de Dependências

```bash
pip install -r requirements.txt
```

---

## Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
OPENAI_API_KEY=sk-seu-token-aqui
GOOGLE_API_KEY=AIza-seu-token-aqui
KIMI_API_KEY=sk-seu-token-aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/ecolmmduel
```

### 2. Segredos do Streamlit

Crie o arquivo `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-seu-token-aqui"
GOOGLE_API_KEY = "AIza-seu-token-aqui"
KIMI_API_KEY = "sk-seu-token-aqui"
DATABASE_URL = "postgresql://usuario:senha@localhost:5432/ecolmmduel"
```

### 3. Estruturação do Diretório de Imagens

Organize os dados de entrada criando o diretório `mamiraua/` na raiz, subdividido em pastas correspondentes à nomenclatura taxonômica exata:

```text
mamiraua/
├── Pantheraonca/
│   ├── img1.jpg
│   └── ...
├── Leoparduswiedii/
├── Sapajusmacrocephalus/
├── Didelphisalbiventris/
├── Sciurusspadiceus/
├── Tupinambisteguixin/
├── Craxglobulosa/
└── Pauxituberosa/
```

### 4. Inicialização do Banco de Dados

```bash
createdb ecolmmduel
psql ecolmmduel < schema.sql
```

---

## Execução e Fluxo de Uso

### Execução da Aplicação

```bash
streamlit run app.py
```

O serviço será iniciado localmente em: `http://localhost:8501`

### Fluxo Operacional

1. **Autenticação**: Identificação do perfil do avaliador.
2. **Sorteio**: Amostragem e exibição de registro fotográfico.
3. **Inferência**: Processamento simultâneo pelas APIs configuradas.
4. **Submissão de Voto**: Análise comparativa e atribuição de preferência técnica.
5. **Classificação**: Atualização algorítmica dos coeficientes de força relativa no ranking.

---

## Tecnologias

| Componente | Tecnologia |
| :--- | :--- |
| **Interface de Usuário** | Streamlit |
| **Linguagem Principal** | Python 3.12 |
| **Camada de Persistência** | PostgreSQL, SQLAlchemy |
| **Provedores de Visão Computacional / IA** | OpenAI API, Google Generative AI, Moonshot AI |
| **Processamento de Dados e Imagens** | Pillow, NumPy |
| **Visualização de Dados** | Altair, Pandas, Matplotlib |
| **Modelagem Estatística de Preferência** | Elo Rating System, Bradley-Terry Model |

---

## Desenvolvimento

### Instalação em Modo Editável

```bash
pip install -e .
```

### Execução da Suíte de Testes

```bash
pytest tests/
```

### Análise Estática de Código

```bash
python -m pylint ai/ data/ ui/ utils/
```

---

## Variáveis de Ambiente

| Variável | Finalidade | Formato de Exemplo |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Autenticação nos serviços OpenAI | `sk-...` |
| `GOOGLE_API_KEY` | Autenticação no Google Cloud / Gemini API | `AIza-...` |
| `KIMI_API_KEY` | Autenticação na API Moonshot | `sk-...` |
| `DATABASE_URL` | String de conexão com o PostgreSQL | `postgresql://user:pass@localhost:5432/db` |

---

## Diretrizes de Segurança e Dados

### Credenciais e Segredos
- O arquivo `.streamlit/secrets.toml` e o arquivo `.env` não devem ser versionados sob nenhuma circunstância.
- Certifique-se de que os arquivos de configuração local constem expressamente no `.gitignore`.
- Utilize gerenciadores de segredos nativos da plataforma de destino ao realizar implantações em ambientes de produção.

### Requisitos de Diretórios
- Para a operação correta do sorteio aleatório, a pasta `mamiraua/` deve estar localizada no nível raiz da aplicação.
- A correspondência entre os identificadores taxonômicos no banco de dados e as subpastas é estrita e sensível a caracteres.

---

## Deploy

O projeto é compatível com implantação no Streamlit Community Cloud.

### Procedimento
1. Envie as alterações validadas para o repositório no GitHub.
2. No painel de controle do Streamlit Cloud, vincule o repositório e selecione a branch principal.
3. Acesse **Advanced Settings -> Secrets** e replique a estrutura definida no seu arquivo `.streamlit/secrets.toml`.
4. Em fluxos que dependam de OAuth, configure a variável `redirect_uri` no painel de segredos para corresponder à URL de produção (ex.: `https://seu-app.streamlit.app/oauth2callback`).
5. Adicione a URI autorizada correspondente no console de credenciais do provedor de autenticação (Google Cloud Console).

---

## Resolução de Problemas

### Erro de CORS / "Origin mismatch"
Caso ocorra bloqueio de requisições originadas fora do domínio estrito de loopback local, configure o arquivo `.streamlit/config.toml`:

```toml
[server]
enableCORS = false
enableXsrfProtection = false
```

---

## Contribuições

Para submeter melhorias ou correções:

1. Realize um fork do repositório.
2. Crie uma branch específica para a demanda (`git checkout -b feature/nome-da-funcionalidade`).
3. Registre seus commits estruturados (`git commit -m 'Implementa melhoria de performance na inferência'`).
4. Envie o branch para o repositório remoto (`git push origin feature/nome-da-funcionalidade`).
5. Abra uma solicitação de Pull Request detalhando as alterações.

---

## Licença

Este software é distribuído sob os termos da licença [MIT](LICENSE).

---

## Contato

- **Desenvolvedor**: Ronald
- **Email**: ronaldvieira614@gmail.com
- **GitHub**: [@Ronald614](https://github.com/Ronald614)

---

## Agradecimentos

- Universidade Federal do Amazonas (UFAM)
- Programa Institucional de Bolsas de Iniciação Científica (PIBIC)
- Instituto de Desenvolvimento Sustentável Mamirauá (IDSM)
