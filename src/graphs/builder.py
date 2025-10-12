import logging
from langgraph.graph import StateGraph, START, END

from src.graphs.response_generation.schemas.MainState import (
  InputState,
  OutputState,
  MainState,
)
from src.graphs.response_generation.nodes.main_bot import (
  main_bot as ResponseGenerationMainBotNode,
)
from src.graphs.response_generation.nodes.formatter import (
  formatter as ResponseGenerationFormatterNode,
)
from src.graphs.response_generation.nodes.input_digest import (
  input_digest as ResponseGenerationInputDigestNode,
)
from langgraph.types import Checkpointer
from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)


def get_response_generation_workflow(
  checkpointer: Checkpointer,
) -> CompiledStateGraph[MainState, None, InputState, OutputState]:
  logger.info("Compiling response generation workflow...")
  return (
    StateGraph(
      state_schema=MainState,
      input_schema=InputState,
      output_schema=OutputState,
    )
    .add_node("input_digest", ResponseGenerationInputDigestNode)
    .add_node("main_bot", ResponseGenerationMainBotNode)
    .add_node("formatter", ResponseGenerationFormatterNode)
    .add_edge(START, "input_digest")
    .add_edge("input_digest", "main_bot")
    .add_edge("main_bot", "formatter")
    .add_edge("formatter", END)
    .compile(name="Response Generation Workflow", checkpointer=checkpointer)
  )

