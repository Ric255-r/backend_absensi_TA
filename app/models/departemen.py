from tortoise import fields
from app.core.audit import AuditableModel


class Departemen(AuditableModel):
  id_departemen = fields.IntField(pk=True)
  nama_departemen = fields.CharField(max_length=100)

  class Meta:
    table = "departemen"

