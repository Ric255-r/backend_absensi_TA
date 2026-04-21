import os
from datetime import datetime, timedelta

from fastapi import HTTPException
from tortoise import Tortoise

from app.models import Subscription

SUBSCRIPTION_STATUS_ACTIVE = "active"
SUBSCRIPTION_STATUS_EXPIRED = "expired"
INTERNAL_JOB_TOKEN_ENV = "INTERNAL_JOB_TOKEN"
SUBSCRIPTION_GRACE_PERIOD_DAYS = 3


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
    WHERE status = %s
      AND TIMESTAMPADD(DAY, %s, end_at) < NOW(6)
    """,
    [
      SUBSCRIPTION_STATUS_EXPIRED,
      SUBSCRIPTION_STATUS_ACTIVE,
      SUBSCRIPTION_GRACE_PERIOD_DAYS,
    ],
  )
  return affected


def get_subscription_grace_end(end_at: datetime) -> datetime:
  return end_at + timedelta(days=SUBSCRIPTION_GRACE_PERIOD_DAYS)


def is_subscription_usable(subscription: Subscription, now: datetime) -> bool:
  if subscription.status != SUBSCRIPTION_STATUS_ACTIVE:
    return False
  return subscription.start_at <= now <= get_subscription_grace_end(subscription.end_at)


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
    or now > get_subscription_grace_end(subscription.end_at)
  ):
    raise HTTPException(
      status_code=403,
      detail="Subscription aplikasi sudah expired.",
    )

  return subscription
