from datetime import date

from pydantic import BaseModel


class HariLiburResponse(BaseModel):
    id_libur: int
    tanggal: date
    keterangan: str
    tipe: str
