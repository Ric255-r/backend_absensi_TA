from tortoise import fields
from app.core.audit import AuditableModel


class PengajuanAbsen(AuditableModel):
  id_pengajuan = fields.IntField(pk=True)
  id_karyawan = fields.CharField(max_length=20)
  karyawan = fields.ForeignKeyField(
    "models.Karyawan",
    related_name="pengajuan_list",
    source_field="id_karyawan",
    on_delete=fields.CASCADE,
  )
  tipe_pengajuan = fields.CharField(max_length=50)
  tanggal_mulai = fields.DateField()
  tanggal_akhir = fields.DateField()
  foto_lampiran = fields.CharField(max_length=255, null=True)
  keterangan = fields.TextField(null=True)
  status = fields.CharField(max_length=20, default="pending")
  alasan_penolakan = fields.TextField(null=True)

  class Meta:
    table = "pengajuan_absen"
