from pydantic import BaseModel


class CheckInRequest(BaseModel):
  latitude_checkin: float
  longitude_checkin: float
  pengajuan: str | None = None

class CheckOutRequest(BaseModel):
  latitude_checkout: float
  longitude_checkout: float
