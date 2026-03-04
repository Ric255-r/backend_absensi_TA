from tortoise import fields
from app.core.audit import AuditableModel


class Absensi(AuditableModel):
  id_absensi = fields.IntField(pk=True)
  tanggal_absen = fields.DatetimeField()
  check_in = fields.DatetimeField(null=True)
  check_out = fields.DatetimeField(null=True)
  latitude_checkin = fields.FloatField(null=True)
  longitude_checkin = fields.FloatField(null=True)
  latitude_checkout = fields.FloatField(null=True)
  longitude_checkout = fields.FloatField(null=True)
  foto_checkin = fields.CharField(max_length=255, null=True)
  foto_checkout = fields.CharField(max_length=255, null=True)
  pengajuan = fields.CharField(max_length=50, null=False)
  is_telat = fields.IntField(default=0)
  status_absen = fields.CharField(max_length=30, default="pending")
  alasan_penolakan = fields.TextField(null=True)
  karyawan = fields.ForeignKeyField(
    "models.Karyawan",
    related_name="absensi_list",
    source_field="id_karyawan",
    on_delete=fields.CASCADE,
  )

  class Meta:
    table = "absensi"
