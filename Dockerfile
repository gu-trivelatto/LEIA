# Usa a imagem oficial do uv com Python 3.12
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Configurações de ambiente
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# --- 1. Instalação de Sistema (Como ROOT) ---
# Adicionamos 'libgbm1' e 'tini' à lista
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    libnss3 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    tini \
    && rm -rf /var/lib/apt/lists/*

# --- 2. Preparação do Usuário ---
RUN useradd -m -u 1000 leia_user
RUN mkdir /app && chown leia_user:leia_user /app

WORKDIR /app

# --- 3. Trocar de usuário ---
USER leia_user

# --- 4. Instalação de Dependências Python ---
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# --- 5. Cópia do Código Fonte ---
COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# --- MUDANÇA IMPORTANTE NO ENTRYPOINT ---
# Usamos o Tini como entrypoint para gerenciar o processo do Chrome
ENTRYPOINT ["/usr/bin/tini", "--"]

# O CMD continua o mesmo
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]