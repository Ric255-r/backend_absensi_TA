from datetime import date, datetime, time
from decimal import Decimal
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Any
from fastapi_jwt import JwtAuthorizationCredentials
from tortoise.models import Model

_audit_actor_ctx: ContextVar[JwtAuthorizationCredentials | dict | None] = ContextVar(
  "audit_actor_ctx",
  default=None,
)
_audit_enabled_ctx: ContextVar[bool] = ContextVar("audit_enabled_ctx", default=False)
_audit_action_ctx: ContextVar[str | None] = ContextVar("audit_action_ctx", default=None)
_audit_metadata_ctx: ContextVar[dict | None] = ContextVar(
  "audit_metadata_ctx",
  default=None,
)


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


def set_audit_actor(actor: JwtAuthorizationCredentials | dict | None) -> None:
  _audit_actor_ctx.set(actor)


def get_current_audit_actor() -> JwtAuthorizationCredentials | dict | None:
  return _audit_actor_ctx.get()


def enable_audit(enabled: bool = True) -> None:
  _audit_enabled_ctx.set(enabled)


def is_audit_enabled() -> bool:
  return _audit_enabled_ctx.get()


@contextmanager
def audit_action(action: str | None, metadata: dict | None = None):
  token_action = _audit_action_ctx.set(action)
  token_metadata = _audit_metadata_ctx.set(metadata)
  try:
    yield
  finally:
    _audit_action_ctx.reset(token_action)
    _audit_metadata_ctx.reset(token_metadata)


def get_current_audit_action() -> str | None:
  return _audit_action_ctx.get()


def get_current_audit_metadata() -> dict | None:
  return _audit_metadata_ctx.get()


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
  from app.models.audit_log import AuditLog

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


class AuditableModel(Model):
  class Meta:
    abstract = True

  async def save(self, *args, **kwargs) -> None:
    if not is_audit_enabled():
      await super().save(*args, **kwargs)
      return

    pk_attr = self._meta.pk_attr
    pk_value = getattr(self, pk_attr, None)
    before_row = None
    is_existing = bool(self._saved_in_db and pk_value is not None)

    if is_existing:
      before_items = (
        await self.__class__.filter(**{pk_attr: pk_value}).limit(1).values()
      )
      before_row = before_items[0] if before_items else None

    await super().save(*args, **kwargs)

    action = get_current_audit_action()
    if action is None and not is_existing:
      return
    if action is None:
      action = "edit"

    new_pk = getattr(self, pk_attr, None)
    after_items = await self.__class__.filter(**{pk_attr: new_pk}).limit(1).values()
    after_row = after_items[0] if after_items else None

    await log_audit(
      actor=get_current_audit_actor(),
      action=action,
      table_name=self._meta.db_table,
      record_id=new_pk,
      before_data=before_row,
      after_data=after_row,
      metadata=get_current_audit_metadata(),
    )

  async def delete(self, *args, **kwargs) -> None:
    if not is_audit_enabled():
      await super().delete(*args, **kwargs)
      return

    pk_attr = self._meta.pk_attr
    pk_value = getattr(self, pk_attr, None)
    before_items = await self.__class__.filter(**{pk_attr: pk_value}).limit(1).values()
    before_row = before_items[0] if before_items else None

    await super().delete(*args, **kwargs)

    action = get_current_audit_action() or "delete"
    await log_audit(
      actor=get_current_audit_actor(),
      action=action,
      table_name=self._meta.db_table,
      record_id=pk_value,
      before_data=before_row,
      after_data=None,
      metadata=get_current_audit_metadata(),
    )
