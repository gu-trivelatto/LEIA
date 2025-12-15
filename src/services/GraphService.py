import logging
from langgraph.graph.state import CompiledStateGraph
from src.graphs.response_generation.schemas.MainState import (
  InputState,
  OutputState,
  MainState,
)
from src.graphs.memories.BaseCheckpointer import BaseCheckpointer
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


def _build_config(chat_id: int | None) -> RunnableConfig:
  return {
    "configurable": {"thread_id": chat_id},
  }


def validate_input(chat_input: str) -> None:
  """
  Valida a entrada do usuário.
  """
  if not chat_input or not chat_input.strip():
    logger.warning("Invalid chat input: empty or whitespace")
  if len(chat_input) > 500:
    logger.warning(
      "Invalid chat input: exceeds maximum length of 500 characters"
    )
  for reset_command in ["reset", "reiniciar", "restart"]:
    if reset_command in chat_input.strip().lower():
      logger.warning("Invalid chat input: reset command detected")
  for suspicius_term in ["prompt"]:
    if suspicius_term in chat_input.strip().lower():
      logger.warning("Invalid chat input: suspicius term detected")
  return


async def invoke_response_generation_graph(
  graph: CompiledStateGraph[MainState, None, InputState, OutputState],
  chat_id: int,
  message_id: int,
  phone_number: str,
  user_name: str,
  user_input: str,
) -> list[dict[str, str]]:
  """
  Invoca o grafo LangGraph com a entrada do usuário e retorna a resposta.
  """
  logger.info(f"Invoking LangGraph with user input: {user_input}")
  try:
    validate_input(user_input)
    state: InputState = {
      "chat_input": user_input,
      "chat_id": chat_id,
      "message_id": message_id,
      "phone_number": phone_number,
      "user_name": user_name
    }
    result = await graph.ainvoke(state, config=_build_config(chat_id))
  except Exception as e:
    logger.error(f"Error invoking LangGraph: {e}", exc_info=True)
    result = {
      "formatted_output": [
        {
          "output": "Ops! Tive um problema, gostaria que eu tentasse novamente?"
        }
      ]
    }
  logger.info(f"LangGraph response: {result}")
  formatted_output = result.get("formatted_output", [])
  agent_reply = (
    formatted_output
    if len(formatted_output) > 0
    else [
      {"output": "Ops! Tive um problema, gostaria que eu tentasse novamente?"}
    ]
  )
  logger.info(f"Agent reply: {agent_reply}")
  return agent_reply


async def reset_conversation_memory(
  checkpointer: BaseCheckpointer, chat_id: int
):
  """
  Deleta todas as chaves associadas a um chat ID no checkpointer.
  """
  logger.info(f"Resetting conversation memory for chat ID: {chat_id}")
  await checkpointer.reset_thread(chat_id)
