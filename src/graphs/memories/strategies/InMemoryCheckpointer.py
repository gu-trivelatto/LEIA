import logging
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from src.graphs.memories.BaseCheckpointer import BaseCheckpointer

logger = logging.getLogger(__name__)


class InMemoryCheckpointer(BaseCheckpointer):
  def __init__(self):
    logger.info("Initializing InMemoryCheckpointer")
    self.checkpointer = InMemorySaver()

  async def get_checkpointer(self) -> BaseCheckpointSaver:
    return self.checkpointer

  async def close(self):
    logger.info("Closing InMemoryCheckpointer")
    # Nothing to close for in-memory saver

  async def open(self):
    logger.info("Opening InMemoryCheckpointer")
    # Nothing to open for in-memory saver

  async def reset_thread(self, thread_id):
    logger.info(f"Resetting thread [{thread_id}] in InMemoryCheckpointer")
    await self.checkpointer.adelete_thread(thread_id)
    logger.info(f"Thread [{thread_id}] reset in InMemoryCheckpointer")
