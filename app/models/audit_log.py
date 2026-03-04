from tortoise import fields
from tortoise.models import Model


class AuditLog(Model):
  id = fields.IntField(pk=True)
  actor_username = fields.CharField(max_length=100, null=True)
  actor_id_karyawan = fields.CharField(max_length=20, null=True)
  actor_role = fields.CharField(max_length=50, null=True)
  action = fields.CharField(max_length=30)
  table_name = fields.CharField(max_length=100)
  record_id = fields.CharField(max_length=100, null=True)
  before_data = fields.JSONField(null=True)
  after_data = fields.JSONField(null=True)
  metadata = fields.JSONField(null=True)
  created_at = fields.DatetimeField(auto_now_add=True)

  class Meta:
    table = "audit_log"
