from tortoise import fields

from app.core.audit import AuditableModel


class Subscription(AuditableModel):
  id_subscription = fields.IntField(pk=True)
  plan_name = fields.CharField(max_length=100, default="default")
  status = fields.CharField(max_length=20, default="active")
  start_at = fields.DatetimeField()
  end_at = fields.DatetimeField()
  expired_at = fields.DatetimeField(null=True)
  notes = fields.CharField(max_length=255, null=True)
  created_at = fields.DatetimeField(auto_now_add=True)
  updated_at = fields.DatetimeField(auto_now=True)

  class Meta:
    table = "subscription"
