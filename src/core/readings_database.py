import logging
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import (
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)
from src.core.config import settings

logger = logging.getLogger(__name__)

DB_OPERATIONS_URL = settings.readings_database.URL.get_secret_value()

async_engine = create_async_engine(DB_OPERATIONS_URL, pool_pre_ping=True)

AsyncSessionMaker = async_sessionmaker(
  bind=async_engine,
  autoflush=False,
  expire_on_commit=False,
  class_=AsyncSession,
)

db_session_context: ContextVar[AsyncSession] = ContextVar("db_session_context")


def get_db_session() -> AsyncSession:
  """Retorna a sessão de banco de dados do contexto da requisição atual."""
  session = db_session_context.get(None)
  if session is None:
    raise Exception("Nenhuma sessão de banco de dados encontrada no contexto.")
  return session