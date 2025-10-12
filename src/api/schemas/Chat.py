from pydantic import BaseModel


class ChatRequest(BaseModel):
  chat_id: int
  chat_input: str
