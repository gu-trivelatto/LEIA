# 1. Base Alpine
FROM alpine:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    BROWSER_PATH="/usr/bin/chromium-headless-shell" \
    CHROME_BIN="/usr/bin/chromium-headless-shell" \
    CHROME_PATH="/usr/bin/chromium-headless-shell"

# 2. Instalação de Infraestrutura e DBus
# Adicionado: dbus
RUN apk add --no-cache \
    python3 \
    chromium-headless-shell \
    freetype \
    ttf-freefont \
    font-noto-emoji \
    harfbuzz \
    nss \
    ca-certificates \
    dbus

# 3. Configuração do DBus (Essencial!)
# O DBus precisa de um machine-id gerado para iniciar.
# Fazemos isso como root antes de mudar de usuário.
RUN mkdir -p /run/dbus
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN dbus-daemon --system --nofork --nopidfile &

# 4. Configuração de Usuário
RUN adduser -D -u 1000 -h /app leia_user

WORKDIR /app

# 5. Troca para usuário não-root
USER leia_user

# 6. Instalação de Dependências
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# 7. Cópia do Código
COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# 8. CMD modificado para usar DBus
# Usamos 'dbus-run-session --' antes do comando.
# Isso inicia o daemon do dbus, configura o ENV DBUS_SESSION_BUS_ADDRESS
# e executa o uvicorn dentro dessa sessão.
CMD ["dbus-run-session", "--", "uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]