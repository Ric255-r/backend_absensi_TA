from pydantic import BaseModel


class LoginResponse(BaseModel):
  data_user: dict
  access_token: str
  refresh_token: str


class ConfirmBindResponse(BaseModel):
  status: str = "ok"
  message: str
