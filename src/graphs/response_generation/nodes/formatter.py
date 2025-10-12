import logging
from src.graphs.llm.model import create_llm
from src.graphs.response_generation.schemas.MainState import MainState
from langchain_core.prompts import ChatPromptTemplate
from src.core.config import settings
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import HumanMessage, AIMessage
from src.core.prompt import PromptHandler

logger = logging.getLogger(__name__)

parser = JsonOutputParser()
prompt = ChatPromptTemplate.from_messages(
  [
    (
      "system",
      PromptHandler().get_prompt(
        settings.formatter_llm.PROMPT_NAME
      ),
    ),
    ("user", "{input}"),
  ]
)
llm = create_llm(
  settings.formatter_llm.MODEL,
  settings.formatter_llm.API_KEY,
  settings.formatter_llm.TEMPERATURE,
  settings.formatter_llm.TIMEOUT,
)
formatter_chain = prompt | llm | parser


def formatter(state: MainState) -> MainState:
  logger.info("Formatting state...")
  messages = state.get("messages", [])
  agent_answer = ""

  if messages:
    last_msg = messages[-1]
    if isinstance(last_msg, (HumanMessage, AIMessage)):
      logger.info(f"Last message content: {last_msg.content}")
      agent_answer = last_msg.content
    elif isinstance(last_msg, dict) and "content" in last_msg:
      logger.info(f"Last message content: {last_msg['content']}")
      agent_answer = last_msg["content"]
    elif isinstance(last_msg, str):
      logger.info(f"Last message content: {last_msg}")
      agent_answer = last_msg

  logger.info(f"Agent answer: {agent_answer}")
  result = formatter_chain.invoke({"input": agent_answer})
  logger.info(f"Formatter result: {result}")
  state["formatted_output"] = result["messages"]
  return state
