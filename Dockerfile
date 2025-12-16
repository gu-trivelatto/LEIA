# Usa a imagem oficial do uv com Python 3.12
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Configurações de ambiente
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# --- 1. Instalação de Sistema (Como ROOT) ---
# Precisamos ser root para apt-get. Fazemos isso primeiro.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    libnss3 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# --- 2. Preparação do Usuário (Ainda como ROOT) ---
# Cria o usuário
RUN useradd -m -u 1000 leia_user

# Cria o diretório de trabalho e JÁ define o dono
# Isso é rápido porque a pasta está vazia
RUN mkdir /app && chown leia_user:leia_user /app

# Define o diretório de trabalho
WORKDIR /app

# --- 3. A Mágica: Trocar de usuário AGORA ---
# A partir daqui, tudo roda como 'leia_user'.
# Os arquivos criados (venv, locks) já pertencerão a ele.
USER leia_user

# --- 4. Instalação de Dependências Python ---
# Copiamos os arquivos com a flag --chown para garantir
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./

# Instala as dependências. 
# Como estamos rodando como 'leia_user', o .venv criado será do 'leia_user'.
# NÃO PRECISA DE CHOWN DEPOIS.
RUN uv sync --frozen --no-install-project --no-dev

# --- 5. Cópia do Código Fonte ---
COPY --chown=leia_user:leia_user . .

# Sincroniza o projeto final
RUN uv sync --frozen --no-dev

# Define o PATH para o venv criado
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]