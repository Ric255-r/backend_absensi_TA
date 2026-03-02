from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
  username: str
  passwd: str
  device_id: str | None = None
  is_admin: int | None = None


class PasswordUpdateRequest(BaseModel):
  old_pass: str = Field(min_length=1)
  new_pass: str = Field(min_length=1)
