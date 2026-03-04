from tortoise import fields
from app.core.audit import AuditableModel


class HariLibur(AuditableModel):
  id_libur = fields.IntField(pk=True)
  tanggal = fields.DateField()
  keterangan = fields.CharField(max_length=255)
  tipe = fields.CharField(max_length=50)

  class Meta:
    table = "hari_libur"

