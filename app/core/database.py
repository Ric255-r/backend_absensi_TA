from tortoise import Tortoise

from app.core.config import build_mysql_dsn, read_db_config


def get_tortoise_config() -> dict:
  config = read_db_config()
  db_url = build_mysql_dsn(config)

  return {
    "connections": {"default": db_url},
    "apps": {
      "models": {
        "models": ["app.models", "aerich.models"],
        "default_connection": "default",
      }
    },
    "use_tz": False,
    "timezone": "Asia/Jakarta",
  }


TORTOISE_ORM = get_tortoise_config()


def init_tortoise(app) -> None:
  async def _startup() -> None:
    await Tortoise.init(config=TORTOISE_ORM)

  async def _shutdown() -> None:
    await Tortoise.close_connections()

  app.add_event_handler("startup", _startup)
  app.add_event_handler("shutdown", _shutdown)
