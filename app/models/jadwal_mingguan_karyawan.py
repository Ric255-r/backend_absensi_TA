from tortoise import fields
from tortoise.models import Model


class JadwalMingguanKaryawan(Model):
  id = fields.IntField(pk=True)
  karyawan = fields.ForeignKeyField(
    "models.Karyawan",
    related_name="jadwal_mingguan_list",
    source_field="id_karyawan",
    on_delete=fields.CASCADE,
  )
  hari = fields.CharField(max_length=20)
  kode_shift = fields.CharField(max_length=20, default="pagi")

  class Meta:
    table = "jadwal_mingguan_karyawan"
