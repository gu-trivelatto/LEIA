from langgraph.prebuilt import create_react_agent
from src.graphs.response_generation.schemas.MainState import MainState
from src.graphs.llm.model import create_llm
from src.core.prompt import PromptHandler
from src.core.config import settings

bot = create_react_agent(
  model=create_llm(
    settings.main_llm.MODEL,
    settings.main_llm.API_KEY,
    settings.main_llm.TEMPERATURE,
    settings.main_llm.TIMEOUT,
  ),
  tools=[sum],
  name=settings.bot.NAME,
  prompt=PromptHandler().get_prompt(
    settings.main_llm.PROMPT_NAME
  ),
  state_schema=MainState,
)


async def main_bot(state: MainState) -> MainState:
  response = await bot.ainvoke(state)
  return {
    **state,
    "messages": response["messages"],
    "messages_history": response["messages_history"],
  }
