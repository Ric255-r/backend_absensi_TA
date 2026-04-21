from datetime import datetime

from fastapi import HTTPException
from fastapi_jwt import JwtAuthorizationCredentials

from app.core.audit import audit_action
from app.core.subscription import (
  SUBSCRIPTION_STATUS_ACTIVE,
  SUBSCRIPTION_STATUS_EXPIRED,
  expire_due_subscriptions,
  get_effective_subscription,
  get_subscription_grace_end,
  is_subscription_usable,
)
from app.models import AuditLog, Subscription
from app.schemas.requests.admin import (
  SubscriptionCreateRequest,
  SubscriptionExpireRequest,
  SubscriptionExtendRequest,
)


def _token_subject(auth_user: JwtAuthorizationCredentials | dict) -> dict:
  return auth_user.subject if hasattr(auth_user, "subject") else auth_user


def _parse_datetime(value: str, field_name: str) -> datetime:
  try:
    return datetime.fromisoformat(value)
  except ValueError:
    raise HTTPException(
      status_code=422,
      detail=f"{field_name} harus berformat ISO datetime, contoh: 2026-04-21T08:00:00",
    )


def _serialize_subscription(subscription: Subscription | None) -> dict | None:
  if not subscription:
    return None

  now = datetime.now()
  grace_end_at = get_subscription_grace_end(subscription.end_at)
  is_in_grace = subscription.end_at < now <= grace_end_at
  is_usable = is_subscription_usable(subscription, now)

  return {
    "id_subscription": subscription.id_subscription,
    "plan_name": subscription.plan_name,
    "status": subscription.status,
    "effective_status": (
      "grace_period"
      if is_in_grace and subscription.status == SUBSCRIPTION_STATUS_ACTIVE
      else subscription.status
    ),
    "start_at": subscription.start_at,
    "end_at": subscription.end_at,
    "grace_end_at": grace_end_at,
    "expired_at": subscription.expired_at,
    "notes": subscription.notes,
    "created_at": subscription.created_at,
    "updated_at": subscription.updated_at,
    "is_usable": is_usable,
    "days_remaining": max((subscription.end_at.date() - now.date()).days, 0),
    "grace_days_remaining": max((grace_end_at.date() - now.date()).days, 0),
  }


async def expire_subscription_job() -> dict:
  affected_rows = await expire_due_subscriptions()
  subscription = await get_effective_subscription(now=datetime.now())

  return {
    "status": "ok",
    "message": "Subscription expire job selesai dijalankan",
    "updated_rows": affected_rows,
    "current_subscription": (
      {
        "id_subscription": subscription.id_subscription,
        "plan_name": subscription.plan_name,
        "status": subscription.status,
        "start_at": subscription.start_at,
        "end_at": subscription.end_at,
        "expired_at": subscription.expired_at,
      }
      if subscription
      else None
    ),
  }


async def get_subscription_status() -> dict:
  await expire_due_subscriptions()
  subscription = await get_effective_subscription(now=datetime.now())

  return {
    "status": "ok",
    "subscription": _serialize_subscription(subscription),
  }


async def list_subscriptions(limit: int = 25) -> dict:
  rows = await Subscription.all().order_by("-start_at", "-id_subscription").limit(limit)
  return {
    "status": "ok",
    "data": [_serialize_subscription(row) for row in rows],
  }


async def get_subscription_history(id_subscription: int) -> dict:
  subscription = await Subscription.filter(id_subscription=id_subscription).first()
  if not subscription:
    raise HTTPException(status_code=404, detail="Subscription tidak ditemukan")

  rows = await AuditLog.filter(
    table_name="subscription",
    record_id=str(id_subscription),
  ).order_by("-created_at", "-id").values(
    "id",
    "actor_username",
    "actor_id_karyawan",
    "actor_role",
    "action",
    "table_name",
    "record_id",
    "before_data",
    "after_data",
    "metadata",
    "created_at",
  )

  return {
    "status": "ok",
    "subscription": _serialize_subscription(subscription),
    "history": [
      {
        **row,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
      }
      for row in rows
    ],
  }


async def create_subscription(
  payload: SubscriptionCreateRequest,
  actor: JwtAuthorizationCredentials,
) -> dict:
  start_at = _parse_datetime(payload.start_at, "start_at")
  end_at = _parse_datetime(payload.end_at, "end_at")
  if end_at <= start_at:
    raise HTTPException(status_code=400, detail="end_at harus lebih besar dari start_at")

  with audit_action("create", {"activity": "subscription_create"}):
    subscription = await Subscription.create(
      plan_name=payload.plan_name,
      status=SUBSCRIPTION_STATUS_ACTIVE,
      start_at=start_at,
      end_at=end_at,
      notes=payload.notes,
    )

  subject = _token_subject(actor)
  return {
    "status": "ok",
    "message": f"Subscription berhasil dibuat oleh {subject.get('username')}",
    "data": _serialize_subscription(subscription),
  }


async def extend_subscription(
  id_subscription: int,
  payload: SubscriptionExtendRequest,
  actor: JwtAuthorizationCredentials,
) -> dict:
  subscription = await Subscription.filter(id_subscription=id_subscription).first()
  if not subscription:
    raise HTTPException(status_code=404, detail="Subscription tidak ditemukan")

  new_end_at = _parse_datetime(payload.end_at, "end_at")
  if new_end_at <= subscription.end_at:
    raise HTTPException(
      status_code=400,
      detail="end_at baru harus lebih besar dari end_at subscription saat ini",
    )

  subscription.end_at = new_end_at
  subscription.status = SUBSCRIPTION_STATUS_ACTIVE
  subscription.expired_at = None
  if payload.notes is not None:
    subscription.notes = payload.notes

  with audit_action("extend", {"activity": "subscription_extend"}):
    await subscription.save()

  subject = _token_subject(actor)
  return {
    "status": "ok",
    "message": f"Subscription berhasil diperpanjang oleh {subject.get('username')}",
    "data": _serialize_subscription(subscription),
  }


async def expire_subscription(
  id_subscription: int,
  payload: SubscriptionExpireRequest,
  actor: JwtAuthorizationCredentials,
) -> dict:
  subscription = await Subscription.filter(id_subscription=id_subscription).first()
  if not subscription:
    raise HTTPException(status_code=404, detail="Subscription tidak ditemukan")

  now = datetime.now()
  subscription.status = SUBSCRIPTION_STATUS_EXPIRED
  subscription.expired_at = subscription.expired_at or now
  if payload.notes is not None:
    subscription.notes = payload.notes

  with audit_action("expire", {"activity": "subscription_expire"}):
    await subscription.save()

  subject = _token_subject(actor)
  return {
    "status": "ok",
    "message": f"Subscription berhasil di-expire oleh {subject.get('username')}",
    "data": _serialize_subscription(subscription),
  }
