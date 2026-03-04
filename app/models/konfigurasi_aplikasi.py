from tortoise import fields
from app.core.audit import AuditableModel


class KonfigurasiAplikasi(AuditableModel):
  id_pengaturan = fields.IntField(pk=True)
  toleransi_terlambat = fields.IntField(default=0)
  maks_hari_cuti = fields.IntField(default=12)

  class Meta:
    table = "konfigurasi_aplikasi"

