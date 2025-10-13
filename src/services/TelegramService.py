import logging
from telegram import Message, Bot
from src.graphs.response_generation.schemas.MainState import InputState, MainState, OutputState
from src.services import GraphService, InputProcessor
from src.core.config import settings
from langgraph.graph.state import CompiledStateGraph
from src.graphs.memories.BaseCheckpointer import BaseCheckpointer

logger = logging.getLogger(__name__)
bot = Bot(token=settings.bot.TELEGRAM_TOKEN.get_secret_value())


async def generate_and_send_response(
  graph: CompiledStateGraph[MainState, None, InputState, OutputState],
  checkpointer: BaseCheckpointer,
  message: Message,
) -> None:
  """
  Invokes the response generation graph and returns the replies.
  """
  logger.info(f"Processing message from chat ID: {message.chat.id}")
  processed_input = await InputProcessor.process_input(message)
  
  if processed_input["chat_input"] == "!reset":
    logger.info(f"Received reset request for chat ID: {message.chat.id}")
    await GraphService.reset_conversation_memory(
      checkpointer, message.chat.id
    )
    replies = [{"output": "Conversa reiniciada!"}]
  else:
    logger.info(f"Invoking response generation graph for chat ID: {message.chat.id}")
    replies = await GraphService.invoke_response_generation_graph(
      graph,
      processed_input["chat_id"],
      processed_input["phone_number"],
      processed_input["chat_input"],
    )
  
  for reply in replies:
    if reply.get("output"):
      logger.info(f"Sending message to chat ID {processed_input['chat_id']}")
      await bot.send_message(chat_id=processed_input["chat_id"], text=reply["output"])
    elif reply.get("filePath"):
      logger.info(f"Sending image with path {reply['filePath']} to chat ID {processed_input['chat_id']}")
      await bot.send_photo(chat_id=processed_input["chat_id"], photo=open(reply["filePath"], 'rb'))
  
  return