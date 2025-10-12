# Labi Bot FastAPI

Projeto de TCC com o objetivo de criar um bot assistente de laboratório, o Labi, utilizando LangGraph e FastAPI. O bot integra diferentes possibilidades de providers de LLM, com estratégias padronizadas de memória e prompts definidos localmente.

---

## Resumo Geral

Este projeto inicializa um bot assistente de laboratório (Labi) com as seguintes características:

- **Grafo de estados** (LangGraph) para controle de fluxo conversacional.
- **FastAPI** para exposição de endpoints REST.
- **Memória plugável** (in-memory, Postgres).
- **Prompts locais** (Arquivos locais `.md`).

---

## Sobre o projeto

### Estrutura geral

- `main.py`: Inicialização FastAPI, ciclo de vida, integração com observabilidade e grafos.
- `src/core/config.py`: Carregamento de configurações, leitura do `.env`, setup de logging, etc.
- `src/api/routers/`: Endpoints REST (`/chat`, `/reset`, `/health`).
- `src/graphs/`: Lógica dos grafos, prompts, estratégias de memória.
- `src/graphs/prompts/`: Prompts locais em `.md`.
- `src/graphs/memories/`: Estratégias de persistência de memória (in_memory, postgres).
- `src/graphs/builder.py`: Montagem dos grafos de workflow.

### Endpoints base do bot

- `POST /bot/chat`: Gera resposta do agente para uma ou mais mensagens.
- `POST /bot/reset`: Reinicia o histórico de uma conversa.
- `GET /health`: Healthcheck do serviço.

---

## Como rodar?

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/gu-trivelatto/labi-tcc.git
   cd api-esit
   ```
2. **Crie e configure o arquivo `.env`:**
   - Use o exemplo fornecido e ajuste as chaves de API, URLs e parâmetros do bot.
3. **Crie o ambiente virtual e instale as dependências:**
   ```bash
   uv venv .venv
   uv pip install -e ".[dev]"
   # ou apenas:
   uv pip install .
   ```
   > O comando `uv venv .venv` cria e ativa o ambiente virtual automaticamente.
   > O arquivo `pyproject.toml` é usado para gerenciar as dependências.
4. **Execute o servidor:**
   ```bash
   uv run -- uvicorn main:app --reload
   ```
5. **Acesse a documentação interativa:**

   - [http://localhost:8000/](http://localhost:8000/) (Swagger UI)
   - [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)

---
