from tortoise import fields
from tortoise.models import Model


class Karyawan(Model):
  id_karyawan = fields.CharField(pk=True, max_length=20)
  nama_karyawan = fields.CharField(max_length=150)
  email_karyawan = fields.CharField(max_length=150, null=True)
  nomor_hp = fields.CharField(max_length=30, null=True)
  foto_profile = fields.CharField(max_length=255, null=True)
  tanggal_rekrut = fields.DateField(null=True)
  status = fields.CharField(max_length=20, default="aktif")
  posisi = fields.CharField(max_length=100, null=True)
  departemen = fields.ForeignKeyField(
    "models.Departemen",
    related_name="karyawan_list",
    source_field="id_departemen",
    on_delete=fields.RESTRICT,
  )

  class Meta:
    table = "karyawan"
