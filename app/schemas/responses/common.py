from pydantic import BaseModel


class APIMessage(BaseModel):
  status: str
  message: str
