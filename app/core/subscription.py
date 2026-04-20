import os
from datetime import datetime

from fastapi import HTTPException
from tortoise import Tortoise

from app.models import Subscription

SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_EXPIRED = "expired"
INTERNAL_JOB_TOKEN_ENV = "INTERNAL_JOB_TOKEN"


def get_internal_job_token() -> str | None:
  return os.getenv(INTERNAL_JOB_TOKEN_ENV)


async def expire_due_subscriptions() -> int:
  conn = Tortoise.get_connection("default")
  affected, _ = await conn.execute_query(
    """
    UPDATE subscription
    SET
      status = %s,
      expired_at = COALESCE(expired_at, NOW(6)),
      updated_at = NOW(6)
    WHERE status = %s AND end_at < NOW(6)
    """,
    [SUBSCRIPTION_STATUS_EXPIRED, SUBSCRIPTION_STATUS_ACTIVE],
  )
  return affected


async def get_effective_subscription(
  now: datetime | None = None,
) -> Subscription | None:
  now = now or datetime.now()

  current_subscription = (
    await Subscription.filter(start_at__lte=now)
    .order_by("-end_at", "-id_subscription")
    .first()
  )
  if current_subscription:
    return current_subscription

  return await Subscription.all().order_by("-start_at", "-id_subscription").first()


async def ensure_active_subscription_or_raise() -> Subscription:
  await expire_due_subscriptions()

  now = datetime.now()
  subscription = await get_effective_subscription(now=now)
  if not subscription:
    raise HTTPException(
      status_code=503,
      detail="Subscription aplikasi belum dikonfigurasi.",
    )

  if subscription.start_at > now:
    raise HTTPException(
      status_code=403,
      detail="Subscription aplikasi belum aktif.",
    )

  if (
    subscription.status != SUBSCRIPTION_STATUS_ACTIVE
    or subscription.end_at < now
  ):
    raise HTTPException(
      status_code=403,
      detail="Subscription aplikasi sudah expired.",
    )

  return subscription
