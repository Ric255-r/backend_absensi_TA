from tortoise import fields
from tortoise.models import Model


class Departemen(Model):
  id_departemen = fields.IntField(pk=True)
  nama_departemen = fields.CharField(max_length=100)

  class Meta:
    table = "departemen"
