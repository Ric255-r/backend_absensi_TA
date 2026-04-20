from datetime import datetime

from app.core.subscription import expire_due_subscriptions, get_effective_subscription


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
