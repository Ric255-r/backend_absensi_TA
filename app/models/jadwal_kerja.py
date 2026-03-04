from tortoise import fields
from tortoise.models import Model


class JadwalKerja(Model):
  id_jadwal = fields.IntField(pk=True)
  nama_shift = fields.CharField(max_length=20, default="pagi")
  hari_dalam_seminggu = fields.CharField(max_length=20)
  shift_mulai = fields.TimeField(null=True)
  shift_selesai = fields.TimeField(null=True)

  class Meta:
    table = "jadwal_kerja"
