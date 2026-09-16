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
