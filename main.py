import logging
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from src.api.routers import health
from src.api.routers import bot
from src.api.routers import telegram
from src.graphs.builder import (
  get_response_generation_workflow,
)
from src.graphs.memories.checkpointer import get_base_checkpointer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
  try:
    logger.info("Iniciando a aplicação...")
    app.state.base_checkpointer = get_base_checkpointer()
    await app.state.base_checkpointer.open()
    logger.info("Conexão de checkpointer aberta com sucesso.")
    checkpointer = await app.state.base_checkpointer.get_checkpointer()
    app.state.response_generation_graph = get_response_generation_workflow(
      checkpointer
    )
    logger.info("Grafo de geração de respostas compilado com sucesso")
  except Exception:
    logger.critical(
      "Falha crítica durante a inicialização da aplicação.", exc_info=True
    )
    raise

  yield

  logger.info("Aplicação sendo finalizada...")
  try:
    if hasattr(app.state, "base_checkpointer") and app.state.base_checkpointer:
      await app.state.base_checkpointer.close()
      logger.info("Conexão de checkpointer encerrada com sucesso.")
  except Exception:
    logger.error("Erro ao fechar a conexão do checkpointer.", exc_info=True)
  logger.info("Processo de finalização da aplicação concluído.")


app = FastAPI(
  title="labi-bot",
  description="Agente conversacional assitente de laboratório",
  version="1.0.0",
  lifespan=lifespan,
  docs_url="/",
  redoc_url="/redoc",
)

app.include_router(health.router, tags=["Health"])
app.include_router(bot.router, prefix="/bot", tags=["Bot"])
app.include_router(telegram.router, prefix="/telegram", tags=["Telegram"])
