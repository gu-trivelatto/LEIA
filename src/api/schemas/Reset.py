from pydantic import BaseModel


class ResetRequest(BaseModel):
  chat_id: int
