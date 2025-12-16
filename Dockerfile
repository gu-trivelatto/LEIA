# 1. Usamos a imagem FULL do Debian 12 (Bookworm)
# Essa imagem é maior, mas tem as libs de sistema (glibc, openssl, etc) completas.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# 2. Instalação de Infraestrutura Gráfica
# Instalamos o Chromium do sistema para garantir que TODAS as libs compartilhadas (.so)
# necessárias para renderização existam. Também instalamos fontes para os gráficos não ficarem com quadrados.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    libnss3 \
    libgbm1 \
    libasound2 \
    tini \
    && rm -rf /var/lib/apt/lists/*

# 3. Configuração de Usuário (Segurança)
RUN useradd -m -u 1000 leia_user && \
    mkdir -p /app && \
    chown -R leia_user:leia_user /app

WORKDIR /app

# 4. Troca para usuário não-root
USER leia_user

# 5. Instalação de Dependências Python
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# 6. Cópia do Código
COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

# Adiciona o venv ao PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV BROWSER_PATH="/usr/bin/chromium"

EXPOSE 8000

# 7. Entrypoint com Tini
# O Tini gerencia os processos do Chromium para evitar zumbis e crashes silenciosos
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]