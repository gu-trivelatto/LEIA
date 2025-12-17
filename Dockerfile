FROM alpine:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    BROWSER_PATH="/usr/bin/chromium-headless-shell" \
    CHROME_BIN="/usr/bin/chromium-headless-shell" \
    CHROME_PATH="/usr/bin/chromium-headless-shell"

RUN apk add --no-cache \
    python3 \
    freetype \
    ttf-freefont \
    font-noto-emoji \
    harfbuzz \
    nss \
    ca-certificates

RUN adduser -D -u 1000 -h /app leia_user

WORKDIR /app

USER leia_user

COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
