import logging
from fastapi import APIRouter, Request

from src.core.security import validate_security

from ..schemas.Chat import ChatRequest
from ..schemas.Reset import ResetRequest
from ...services import GraphService

from fastapi import Depends

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
  "/chat",
  response_model=list[dict[str, str]],
  summary="Gera uma resposta do agente",
  dependencies=[Depends(validate_security)],
)
async def chat(request: Request, body: ChatRequest):
  """
  Recebe uma mensagem e um ID de chat, invoca o agente e retorna a resposta.
  """
  logger.info(
    f"Received chat request with chat ID: {body.chat_id} and input: {body.chat_input}"
  )
  replies = await GraphService.invoke_response_generation_graph(
    request.app.state.response_generation_graph,
    body.chat_id,
    "",
    body.chat_input,
  )
  return replies


@router.post(
  "/reset",
  response_model=list[dict[str, str]],
  summary="Reinicia uma conversa",
  dependencies=[Depends(validate_security)],
)
async def reset(request: Request, body: ResetRequest):
  """
  Apaga o histórico de uma conversa baseado no ID de chat.
  """
  logger.info(f"Received reset request for chat ID: {body.chat_id}")
  await GraphService.reset_conversation_memory(
    request.app.state.base_checkpointer, body.chat_id
  )
  return [{"output": "Conversa reiniciada!"}]
