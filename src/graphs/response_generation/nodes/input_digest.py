import logging
from ..schemas.MainState import MainState
from langchain.schema import HumanMessage
from src.core.config import settings

logger = logging.getLogger(__name__)


async def input_digest(state: MainState) -> MainState:
  processed_input = state["chat_input"]
  
  if not state.get("messages_history"):
    state["messages_history"] = []
  # Adiciona a nova mensagem ao histórico completo
  state["messages_history"].append(HumanMessage(content=processed_input))
  # Limita o que vai para o próximo estado
  state["messages"] = [HumanMessage(content=processed_input)]
  clean_messages = state["messages"][-settings.bot.MAX_HISTORY :]
  return {**state, "messages": clean_messages}
