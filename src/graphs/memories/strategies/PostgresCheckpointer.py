import asyncio
import logging
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from psycopg.rows import dict_row, DictRow
from src.core.config import settings
from src.graphs.memories.BaseCheckpointer import BaseCheckpointer

logger = logging.getLogger(__name__)


class PostgresCheckpointer(BaseCheckpointer):
  def __init__(self):
    logger.info("Initializing PostgresCheckpointer")
    self.pool: AsyncConnectionPool[AsyncConnection[DictRow]] = (
      AsyncConnectionPool(
        conninfo=settings.memory.URL.get_secret_value(),
        max_size=20,
        open=False,
        kwargs={"row_factory": dict_row},
      )
    )
    self.checkpointer = AsyncPostgresSaver(self.pool)

  async def get_checkpointer(self) -> BaseCheckpointSaver:
    return self.checkpointer

  async def close(self):
    try:
      logger.info("Closing PostgresCheckpointer")
      await self.pool.close()
    except Exception as e:
      logger.error(f"Error closing PostgresCheckpointer: {e}")

  def _run_sync_setup(self):
    """Executa o setup do DB de forma síncrona em um thread separado."""
    if settings.memory.DISABLE_MIGRATIONS:
      logger.info(
        "Migrations are disabled in settings. Skipping database setup."
      )
      return
    logger.info("[Sync Setup] Running initial database setup...")
    db_uri = settings.memory.URL
    try:
      with psycopg.connect(db_uri.get_secret_value(), autocommit=True) as conn:
        logger.info(
          "[Sync Setup] Temporary connection with AUTOCOMMIT=True established."
        )
        setup_checkpointer = PostgresSaver(conn)  # type: ignore

        logger.info("[Sync Setup] Executing LangGraph .setup()...")
        setup_checkpointer.setup()

        logger.info(
          "\033[92m[Sync Setup] Database setup completed successfully!\033[0m"
        )
    except Exception as e:
      logger.error(
        f"FATAL: [Sync Setup] Database setup failed: {e}", exc_info=True
      )
      raise

  async def open(self):
    await asyncio.to_thread(self._run_sync_setup)
    logger.info("Opening PostgresCheckpointer")
    await self.pool.open()

  async def reset_thread(self, thread_id):
    logger.info(f"Resetting thread [{thread_id}] in PostgresCheckpointer")
    async with self.pool.connection() as conn:
      await conn.execute(
        "DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,)
      )
      await conn.execute(
        "DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,)
      )
      await conn.execute(
        "DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,)
      )
      await conn.commit()
    logger.info(f"Thread [{thread_id}] reset in PostgresCheckpointer")
