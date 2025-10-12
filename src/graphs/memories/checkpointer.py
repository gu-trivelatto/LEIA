import logging
from src.core.config import settings
from typing import Type
from src.graphs.memories.BaseCheckpointer import BaseCheckpointer
from src.graphs.memories.strategies.PostgresCheckpointer import (
  PostgresCheckpointer,
)
from src.graphs.memories.strategies.InMemoryCheckpointer import (
  InMemoryCheckpointer,
)

logger = logging.getLogger(__name__)

STRATEGIES: dict[str, Type[BaseCheckpointer]] = {
  "postgres": PostgresCheckpointer,
  "in_memory": InMemoryCheckpointer,
}


def get_base_checkpointer() -> BaseCheckpointer:
  logger.info(f"Using memory strategy: {settings.memory.STRATEGY}")
  strategy_class = STRATEGIES.get(settings.memory.STRATEGY)
  if not strategy_class:
    logger.error(f"Unknown memory strategy: {settings.memory.STRATEGY}")
    raise ValueError(f"Unknown memory strategy: {settings.memory.STRATEGY}")
  return strategy_class()
