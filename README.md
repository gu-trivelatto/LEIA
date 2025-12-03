# LEIA: Projeto de Tese de Conclusão de Curso (TCC)

Projeto de TCC dos alunos Gustavo Trivelatto Gabriel e Bruno Borges Paschoalinoto do curso de Engenharia de Computação da Escola Politécnica da USP.

O projeto traz como base um projeto anterior do aluno Gustavo Trivelatto Gabriel, onde um agente de IA baseado em LLM foi desenvolvido para auxiliar pesquisadores e pessoas leigas a manipular modelos de sistemas de energia de forma simplificada via linguagem natural, o agente era capaz de alterar parâmetros, executar modelos e comparar resultados a partir de comandos textuais simples através de uma interface gráfica desenvolvida em Python.

Com a orientação do Prof. Dr. Jorge Luis Risco Becerra, foi desenvolvida uma evolução do projeto anterior, alterando o escopo do projeto para observabilidade de consumo energético em um laboratório universitário.

Utilizando dispositivos da Beckhoff já disponíveis no laboratório, foi desenvolvido um sistema capaz de coletar as leituras de consumo energético lidos através dos dispositivos de monitoramento, que em seguida os armazena em um banco de dados relacional que é então disponibilizado para acesso via uma API dedicada. Com essa base de aquisição de dados, o novo agente para o caso de uso em questão pode ser então desenvolvido.

A base em LangGraph do projeto anterior foi melhorada em diversos aspectos, como organização de código, paralelismo, velocidade de execução e melhor controle do fluxo de inferência da LLM. Além disso, a interface gráfica dedicada construída em Python foi deixada de lado em favor de uma API integrada ao aplicativo de mensagens Telegram, de forma que o acesso ao agente agora pode ser feito remotamente através de qualquer smartphone.

O agente é capaz de acessar dados históricos do consumo energético, interpretar os dados coletados, gerar insights e explicações complexos baseados no padrão de consumo e possíveis instabilidades detectados na rede, plottar gráficos coerentes, buscar informações atuais na internet e controlar uma planilha de histórico de manutenções realizadas no laboratório, podendo consultar manutenções passadas, listar manuntenções agendadas e incluir novas.

Na avaliação do projeto foi atingido 96% de precisão nos casos de uso propostos para o conjunto de testes, com um tempo de resposta médio de cerca de 6.2 segundos, comprovando que utilizando modelos de linguagem e frameworks de estado da arte, e provedores de alto desempenho, podemos conseguir níveis de desempenho comparáveis a dashboards tradicionais com potencialmente mais benefícios para o usuário que não precisa necessariamente saber operar dashboards complexos e interpretar grandes volumes de dados para conseguir acompanhar em tempo real o consumo energético do laboratório.

---

## Resumo do projeto

Este projeto inicializa um agente assistente de laboratório (LEIA) com as seguintes características:

- **Grafo de estados** (LangGraph) para controle de fluxo conversacional.
- **FastAPI** para exposição de endpoints REST.
- **Memória plugável** (in-memory, Postgres).
- **Prompts locais** (Arquivos locais `.md`).

---

## Stack

O projeto foi construído focando no provedor de LLM Groq, por conta dos baixos preços, disponibilidade de modelos open weight e alto desempenho com baixa latência. Contudo, a estrutura desenvolvida através do framework LangGraph, parte do LangChain, permite facilmente substituir o provedor por outros que possam vir a oferecer melhores serviços ou até mesmo apenas adicionar provedores extras para aplicações multi provedor ou como fallbacks.

Outros serviços terceiros utilizados são Tavily para buscas na internet e um projeto na Google Cloud para criação de uma conta de serviço para acesso à planilha de manutenções.

Como ponto inicial vindo do projeto original, também temos o esqueleto de uma ferramenta de RAG que utiliza Qdrand e LlamaParse para embeddar arquivos e armazenar os dados vetorizados, contudo, esta funcionalidade não foi incluída inicialmente na LEIA.

## Sobre o projeto

### Estrutura geral

- `main.py`: Inicialização FastAPI, ciclo de vida, integração com observabilidade e grafos.
- `src/core/config.py`: Carregamento de configurações, leitura do `.env`, setup de logging, etc.
- `src/api/routers/`: Endpoints REST (`/chat`, `/reset`, `/health`, `/telegram`).
- `src/graphs/`: Lógica dos grafos, prompts, estratégias de memória.
- `src/graphs/prompts/`: Prompts locais em `.md`.
- `src/graphs/memories/`: Estratégias de persistência de memória (in_memory, postgres).
- `src/graphs/builder.py`: Montagem dos grafos de workflow.
- `src/graphs/response_generation/tools`: Ferramentas utilizadas pelo agente

### Endpoints base do agente

- `GET /health`: Healthcheck do serviço.

#### Endpoints para teste direto do agente

- `POST /bot/chat`: Gera resposta do agente para uma ou mais mensagens.
- `POST /bot/reset`: Reinicia o histórico de uma conversa.

#### Endpoint para operação via Telegram

- `POST /telegram/webhook`: Abre uma rota para receber webhooks do aplicativo Telegram.

---

## Como rodar?

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/gu-trivelatto/LEIA.git
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

## Como expor seu endpoint para testar o Telegram localmente?

1. **Crie uam conta no ngrok**
   - Acesse [ngrok.com](ngrok.com)
   - Crie uma conta clicando em `Sign up`

2. **Instale ngrok**
   - Para distribuições `Debian Linux`, siga os passos a seguir, para outros sistemas acesse o site para mais detalhes
   ```
   curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
      | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
      && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
      | sudo tee /etc/apt/sources.list.d/ngrok.list \
      && sudo apt update \
      && sudo apt install ngrok
   ```

3. **Acesse sua conta e ache seu domínio**
   - Na sua conta, procure pelo seu domínio particular, o ngrok te fornecerá um gratuitamente
   - O domínio se parece com `https://texto-aleatorio.ngrok-free.app`

4. **Abra a porta para acesso público**
   - Com seu servidor FastAPI rodando, execute o seguinte comando para expor a porta publicamente
   ```
   ngrok http 8000
   ```
   - Com isso, já é possível acessar seu servidor através da internet

## Como configurar o webhook do Telegram?

1. **Crie um bot no Telegram**
   - Para configurar um bot, siga o passo a passo [neste tutorial](https://core.telegram.org/bots/tutorial)

2. **Inicie o servidor e exponha a porta**
   - Inicie o servidor FastAPI do bot e execute o ngrok como explicado nos passos anteriores

3. **Execute o script**
   - Altere o script `setup_webhook.sh` para conter o seu botId e o seu link pessoal do ngrok
   - Execute o script para realizar a configuração do webhook
   - Com isso seu bot estará configurado para enviar webhooks para seu servidor
