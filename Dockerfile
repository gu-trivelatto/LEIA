# 1. Base Alpine (Leve e Segura)
FROM alpine:latest

# Instala o 'uv' copiando da imagem oficial (método recomendado e mais rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Define onde o navegador está para bibliotecas como Selenium/Playwright/Pyppeteer
    BROWSER_PATH="/usr/bin/chromium-headless-shell" \
    CHROME_BIN="/usr/bin/chromium-headless-shell" \
    CHROME_PATH="/usr/bin/chromium-headless-shell"

# 2. Instalação de Infraestrutura (APK)
# - python3: Necessário pois o Alpine vem zerado
# - chromium: Navegador compatível com Alpine (substitui o chrome-headless-shell)
# - freetype, ttf-freefont, font-noto-emoji: Fontes essenciais para evitar "quadrados" no render
# --no-cache: Para não guardar cache de instalador e manter a imagem pequena
RUN apk add --no-cache \
    python3 \
    chromium-headless-shell \
    freetype \
    ttf-freefont \
    font-noto-emoji \
    harfbuzz \
    nss \
    ca-certificates

# 3. Configuração de Usuário
# 'adduser' é o comando do Alpine (diferente do useradd do Debian)
# -D: Sem senha
# -u 1000: ID do usuário
# -h /app: Define o diretório home já como /app
RUN adduser -D -u 1000 -h /app leia_user

WORKDIR /app

# 4. Troca para usuário não-root
USER leia_user

# 5. Instalação de Dependências Python
# O uv vai usar o python3 do sistema instalado via apk
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# 6. Cópia do Código
COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

# Adiciona o venv ao PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# 7. Entrypoint Simplificado (Sem Tini)
# Usamos o 'uv run' diretamente como processo principal
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]