import asyncio
import logging
from fastapi import APIRouter, Request
from telegram import Update
from ..schemas.Telegram import TelegramRawUpdate
# TODO converter Update para um modelo pydantic

from src.core.security import validate_security

from ...services import TelegramService

from fastapi import Depends

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
  "/webhook",
  response_model=dict[str, str],
  summary="Gera uma resposta do agente em resposta a um webhook do Telegram",
  dependencies=[Depends(validate_security)],
)
async def webhook(request: Request, body: TelegramRawUpdate):
  """
  Recebe uma mensagem e um ID de chat e trigga a geração de uma resposta.
  """
  update = Update.de_json(body.root, bot=None)
  if update.message and update.message.chat:
    logger.info(
      f"Received request for chat with ID: {update.message.chat.id}"
    )
  else:
    logger.warning("Received request without chat information.")
    raise ValueError("Chat information is required.")
  
  asyncio.create_task(
    TelegramService.generate_and_send_response(
      request.app.state.response_generation_graph,
      request.app.state.base_checkpointer,
      update.message
    )
  )
  return {"status": "Ok"}
