# Usa a imagem oficial do uv com Python 3.12 (Slim - Leve)
# Não precisamos mais da versão full/bookworm nem de chromium!
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Configurações de otimização do Python
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# 1. Preparação do Usuário (Segurança)
# Não precisamos instalar NADA de sistema (apt-get) para o vl-convert rodar.
RUN useradd -m -u 1000 leia_user && \
    mkdir -p /app && \
    chown -R leia_user:leia_user /app

WORKDIR /app

# 2. Troca para usuário não-root
USER leia_user

# 3. Instalação de Dependências
# O vl-convert é um binário Rust que vem dentro do wheel do Python.
# O uv vai instalar ele aqui.
COPY --chown=leia_user:leia_user pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev

# 4. Cópia do Código Fonte
COPY --chown=leia_user:leia_user . .
RUN uv sync --frozen --no-dev

# Adiciona o venv ao PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Comando padrão
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]