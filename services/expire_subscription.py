import asyncio

from tortoise import Tortoise

from app.core.database import TORTOISE_ORM
from app.core.subscription import expire_due_subscriptions


async def main() -> None:
  await Tortoise.init(config=TORTOISE_ORM)
  try:
    affected_rows = await expire_due_subscriptions()
    print(f"Subscription expire job selesai. Updated rows: {affected_rows}")
  finally:
    await Tortoise.close_connections()


if __name__ == "__main__":
  asyncio.run(main())
