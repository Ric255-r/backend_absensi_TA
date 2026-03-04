from tortoise import fields
from app.core.audit import AuditableModel


class Akun(AuditableModel):
  username = fields.CharField(pk=True, max_length=100)
  passwd = fields.CharField(max_length=255)
  roles = fields.CharField(max_length=50, default="karyawan")
  last_login = fields.DatetimeField(null=True)
  device_id = fields.CharField(max_length=255, null=True)
  status = fields.CharField(max_length=20, default="aktif")
  id_karyawan = fields.CharField(
    max_length=20, unique=True
  )  # Field untuk menyimpan ID karyawan
  karyawan = fields.OneToOneField(
    "models.Karyawan",
    related_name="akun",
    source_field="id_karyawan",  # kalau PK ini jadikan source_field, tortoise akan baca aja sbg id tok.
    on_delete=fields.CASCADE,
  )

  class Meta:
    table = "akun"
