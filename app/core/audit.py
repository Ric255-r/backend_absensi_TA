from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from fastapi_jwt import JwtAuthorizationCredentials

from app.models.audit_log import AuditLog


def _normalize_value(value: Any) -> Any:
  if value is None:
    return None
  if isinstance(value, (str, int, float, bool)):
    return value
  if isinstance(value, Decimal):
    return float(value)
  if isinstance(value, (datetime, date, time)):
    return value.isoformat()
  if isinstance(value, dict):
    return {str(k): _normalize_value(v) for k, v in value.items()}
  if isinstance(value, (list, tuple, set)):
    return [_normalize_value(v) for v in value]
  return str(value)


def get_actor_payload(actor: JwtAuthorizationCredentials | dict | None) -> dict:
  if actor is None:
    return {}
  payload = actor.subject if hasattr(actor, "subject") else actor
  if not isinstance(payload, dict):
    return {}
  return payload


async def log_audit(
  *,
  actor: JwtAuthorizationCredentials | dict | None,
  action: str,
  table_name: str,
  record_id: str | int | None = None,
  before_data: dict | list | None = None,
  after_data: dict | list | None = None,
  metadata: dict | None = None,
) -> None:
  payload = get_actor_payload(actor)
  await AuditLog.create(
    actor_username=payload.get("username"),
    actor_id_karyawan=payload.get("id_karyawan"),
    actor_role=payload.get("roles"),
    action=action,
    table_name=table_name,
    record_id=str(record_id) if record_id is not None else None,
    before_data=_normalize_value(before_data),
    after_data=_normalize_value(after_data),
    metadata=_normalize_value(metadata),
  )
