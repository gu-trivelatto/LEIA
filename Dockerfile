FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# --- 1. Instalação de Sistema (Blindada) ---
# Adicionamos bibliotecas cruciais que costumam faltar no slim:
# libxshmfence1, libglu1-mesa, libx11-xcb1, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium-headless-shell \
    fonts-liberation \
    libnss3 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libxshmfence1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libglu1-mesa \
    tini \
    && rm -rf /var/lib/apt/lists/*

# --- 2. Preparação do Usuário ---
RUN useradd -m -u 1000 leia_user
RUN mkdir /app && chown leia_user:leia_user /app

WORKDIR /app

# --- 3. Trocar de usuário ---
USER leia_user

# --- 4. Dependências Python ---
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# --- 5. Código Fonte ---
COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Entrypoint via Tini para evitar processos zumbis do Chrome
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]