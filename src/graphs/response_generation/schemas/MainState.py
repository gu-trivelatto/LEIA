from typing import NotRequired, TypedDict

from langgraph.graph.message import BaseMessage
from langgraph.prebuilt.chat_agent_executor import AgentState


class MainState(AgentState):
  chat_input: str
  chat_id: int
  phone_number: str
  user_name: str
  formatted_output: NotRequired[list[dict[str, str]]]
  messages_history: list[BaseMessage]


class InputState(TypedDict):
  chat_input: str
  chat_id: int
  phone_number: str
  user_name: str


class OutputState(TypedDict):
  formatted_output: list[dict[str, str]]
