from pydantic import BaseModel


class CheckInResponse(BaseModel):
  status: str
  message: str
