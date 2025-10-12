from abc import ABC, abstractmethod

from langgraph.checkpoint.base import BaseCheckpointSaver


class BaseCheckpointer(ABC):
  def __init__(self):
    pass

  @abstractmethod
  async def get_checkpointer(self) -> BaseCheckpointSaver:
    pass

  @abstractmethod
  async def reset_thread(self, thread_id):
    pass

  @abstractmethod
  async def close(self):
    pass

  @abstractmethod
  async def open(self):
    pass
