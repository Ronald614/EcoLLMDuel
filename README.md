# 🦁 EcoLLMDuel

> **Sistema de Avaliação de Modelos de IA para Análise de Imagens de Armadilhas Fotográficas**

Um projeto inovador que utiliza **duelos de IA** para avaliar qual modelo é melhor em identificar e classificar animais selvagens em imagens de armadilhas fotográficas. Combina Streamlit, múltiplas APIs de IA (OpenAI, Google Gemini, Kimi/Moonshot AI) e algoritmos sofisticados de ranking.

## 📋 Índice

- [Características](#-características)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Tecnologias](#-tecnologias)
- [Contribuindo](#-contribuindo)

---

## ✨ Características

✅ **Arena de Duelo**: Compare dois modelos de IA lado a lado  
✅ **Múltiplos Modelos**: Suporte para OpenAI, Google Gemini e Kimi (Moonshot AI)  
✅ **Ranking Inteligente**: Cálculos de Elo Rating e Bradley-Terry  
✅ **Cadastro de Usuários**: Rastreamento de avaliadores com histórico  
✅ **Leaderboard**: Rankings em tempo real dos melhores modelos  
✅ **Análise JSON Estruturada**: Respostas organizadas com nome científico, comum e contagem de indivíduos  
✅ **Timing**: Registro de latência de cada modelo  

---

## 🔧 Pré-requisitos

- **Python 3.12+**
- **PostgreSQL 12+** (para banco de dados)
- **Chaves de API** de:
  - OpenAI (para GPT-4V)
  - Google Cloud (para Gemini)
  - Moonshot AI (para Kimi)

---

## 📥 Instalação

### (1) Clonar o repositório

\`\`\`bash
git clone https://github.com/Ronald614/EcoLLMDuel.git
cd EcoLLMDuel
\`\`\`

### (2) Criar ambiente virtual

\`\`\`bash
python3 -m venv env
\`\`\`

### (3) Ativar o ambiente virtual

**Linux/macOS:**
\`\`\`bash
source env/bin/activate
\`\`\`

**Windows:**
\`\`\`bash
.\env\Scripts\activate
\`\`\`

### (4) Instalar dependências

\`\`\`bash
pip install -r requirements.txt
\`\`\`

---

## ⚙️ Configuração

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

\`\`\`bash
# .env
OPENAI_API_KEY=sk-seu-token-aqui
GOOGLE_API_KEY=AIza-seu-token-aqui
KIMI_API_KEY=sk-seu-token-aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/ecolmmduel
\`\`\`

Ou exporte direto no terminal:

\`\`\`bash
export OPENAI_API_KEY="sk-sua-chave-openai-aqui"
export GOOGLE_API_KEY="AIza-sua-chave-google-aqui"
export KIMI_API_KEY="sk-sua-chave-kimi-aqui"
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/ecolmmduel"
\`\`\`

### 2. Configurar Secrets do Streamlit

Crie o arquivo `.streamlit/secrets.toml`:

\`\`\`toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-seu-token-aqui"
GOOGLE_API_KEY = "AIza-seu-token-aqui"
KIMI_API_KEY = "sk-seu-token-aqui"
DATABASE_URL = "postgresql://usuario:senha@localhost:5432/ecolmmduel"
\`\`\`

### 3. Criar Estrutura de Imagens

Crie a pasta `mamiraua/` com subpastas para cada espécie:

\`\`\`
mamiraua/
├── Pantheraonca/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── ...
├── Leoparduswiedii/
├── Sapajusmacrocephalus/
├── Didelphisalbiventris/
├── Sciurusspadiceus/
├── Tupinambisteguixin/
├── Craxglobulosa/
└── Pauxituberosa/
\`\`\`

### 4. Configurar Banco de Dados

\`\`\`bash
createdb ecolmmduel
psql ecolmmduel < schema.sql  # (se houver arquivo SQL)
\`\`\`

---

## 🚀 Como Usar

### Rodar a Aplicação

\`\`\`bash
streamlit run app.py
\`\`\`

A aplicação abrirá em: **http://localhost:8501**

### Fluxo de Uso

1. **Login/Cadastro**: Autentique-se ou preencha seu perfil
2. **Arena de Duelo**: Clique em "Sortear Novo Duelo"
3. **Análise**: Os modelos analisam a imagem automaticamente
4. **Voto**: Compare as respostas e escolha o melhor modelo
5. **Leaderboard**: Veja o ranking dos modelos em tempo real

---

## 📁 Estrutura do Projeto

\`\`\`
EcoLLMDuel/
├── app.py                 # Ponto de entrada principal
├── streamlit_app.py       # Wrapper do Streamlit
├── config.py              # Configurações globais
├── requirements.txt       # Dependências Python
├── README.md              # Este arquivo
├── .gitignore             # Padrões de git
├── LICENSE                # Licença do projeto
│
├── ai/
│   ├── __init__.py
│   ├── models.py         # Integração com APIs de IA
│   └── prompt.py         # Template do prompt
│
├── data/
│   ├── __init__.py
│   ├── database.py       # Conexão PostgreSQL e CRUD
│   ├── drive.py          # Carregamento de imagens
│   └── ranking.py        # Algoritmos de ranking
│
├── ui/
│   ├── __init__.py
│   ├── arena.py          # Interface da Arena
│   ├── cadastro.py       # Formulário de cadastro
│   ├── ranking.py        # Visualização do Leaderboard
│   └── sidebar.py        # Barra lateral
│
├── utils/
│   ├── __init__.py
│   ├── image.py          # Processamento de imagens
│   ├── json_utils.py     # Parsing de JSON
│   └── session.py        # Gerenciamento de sessão
│
├── .streamlit/
│   └── secrets.toml       # (NÃO commitar!) Variáveis secretas
│
├── env/                   # (NÃO commitar!) Ambiente virtual
└── mamiraua/              # (NÃO commitar!) Dataset de imagens
\`\`\`

---

## 💾 Tecnologias

| Componente | Tecnologia |
|-----------|-----------|
| **Frontend** | Streamlit |
| **Backend** | Python 3.12 |
| **Banco de Dados** | PostgreSQL + SQLAlchemy |
| **APIs de IA** | OpenAI, Google Generative AI, Kimi (Moonshot AI) |
| **Processamento de Imagem** | Pillow, NumPy |
| **Visualização** | Altair, Pandas, Matplotlib |
| **Ranking** | Elo Rating, Bradley-Terry Model |

---

## 📊 Algoritmos de Ranking

### Elo Rating
Sistema clássico de rating baseado em pontos. Cada vitória/derrota ajusta a pontuação dinamicamente.

### Bradley-Terry Model
Modelo probabilístico mais sofisticado que considera a probabilidade de uma IA ser melhor que outra.

---

## 🛠️ Desenvolvimento

### Instalar em modo desenvolvimento

\`\`\`bash
pip install -e .
\`\`\`

### Rodar testes

\`\`\`bash
pytest tests/
\`\`\`

### Verificar sintaxe

\`\`\`bash
python -m pylint ai/ data/ ui/ utils/
\`\`\`

---

## 📝 Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | `sk-...` |
| `GOOGLE_API_KEY` | Chave da API Google | `AIza-...` |
| `KIMI_API_KEY` | Chave da API Moonshot (Kimi) | `sk-...` |
| `DATABASE_URL` | URL do PostgreSQL | `postgresql://user:pass@localhost/db` |

---

## ⚠️ Avisos Importantes

> [!IMPORTANT]
> **Segurança de Chaves de API**
>
> - NUNCA commite o arquivo `.streamlit/secrets.toml`
> - NUNCA exponha suas chaves em logs ou prints
> - Use variáveis de ambiente em produção
> - Revise o `.gitignore` antes de fazer push

> [!WARNING]
> **Estrutura de Imagens**
>
> Para que a funcionalidade de "Sortear Imagem Aleatória" funcione:
> - Crie a pasta `mamiraua/` no diretório raiz
> - Organize imagens em subpastas por espécie
> - Nomes das pastas devem corresponder ao banco de dados

---

## 🚀 Deploy

O projeto está pronto para depoy no **Streamlit Community Cloud**.

### Passos Rápidos
1.  Faça push do código para o GitHub.
2.  No Streamlit Cloud, conecte seu repositório.
3.  Vá em **Advanced Settings -> Secrets** e cole o conteúdo do seu `.streamlit/secrets.toml`.
4.  Atualize a `redirect_uri` no secrets do Cloud para a URL final do app (ex: `https://seu-app.streamlit.app/oauth2callback`).
5.  Adicione essa mesma URL no Google Cloud Console (OAuth).

Para um guia detalhado, consulte o arquivo [deployment_plan.md](deployment_plan.md).

---

## ❓ Troubleshooting

### Erro "Origin mismatch"
Se você ver esse erro rodando localmente, é porque o Streamlit está bloqueando conexões de IPs diferentes de localhost.
O projeto já inclui um arquivo `.streamlit/config.toml` (criado localmente) para corrigir isso em desenvolvimento. Se o erro persistir, verifique se esse arquivo existe com:

```toml
[server]
enableCORS = false
enableXsrfProtection = false
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).

---

## 📧 Contato

**Desenvolvedor**: Ronald  
**Email**: seu-email@example.com  
**GitHub**: [@Ronald614](https://github.com/Ronald614)

---

## 🙏 Agradecimentos

- Universidade Federal do Amazonas (UFAM)
- PIBIC - Programa Institucional de Bolsas de Iniciação Científica
- Mamirauá Instituto de Desenvolvimento Sustentável

---

**Última atualização**: 9 de fevereiro de 2026
