from langgraph.prebuilt import create_react_agent
from src.graphs.response_generation.schemas.MainState import MainState
from src.graphs.llm.model import create_llm
from src.core.prompt import PromptHandler
from src.core.config import settings
from datetime import datetime
from src.graphs.response_generation.tools.DataAccess import DataAccess
from src.graphs.response_generation.tools.WebSearch import WebSearch
from src.graphs.response_generation.tools.MaintenanceSheet import MaintenanceSheet


async def main_bot(state: MainState) -> MainState:
  now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
  
  complete_prompt = PromptHandler().get_prompt(
    settings.main_llm.PROMPT_NAME
  )
  complete_prompt += "\n\nO nome do usuário é: " + state["user_name"]
  complete_prompt += "\nA data e hora atual é: " + now + "\n"
  
  bot = create_react_agent(
    model=create_llm(
      settings.main_llm.MODEL,
      settings.main_llm.API_KEY,
      settings.main_llm.TEMPERATURE,
      settings.main_llm.TIMEOUT,
    ),
    tools=[
      DataAccess,
      WebSearch,
      MaintenanceSheet,
    ],
    name=settings.bot.NAME,
    prompt=complete_prompt,
    state_schema=MainState,
  )
  
  response = await bot.ainvoke(state)
  return {
    **state,
    "messages": response["messages"],
    "messages_history": response["messages_history"],
  }
