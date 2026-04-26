import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_STORAGE_DIR = BASE_DIR / "storage" / "uploads"

load_dotenv(BASE_DIR / ".env")


def get_env_bool(name: str, default: bool = False) -> bool:
  raw_value = os.getenv(name)
  if raw_value is None:
    return default
  return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_env_str(name: str, default: str | None = None) -> str | None:
  value = os.getenv(name)
  if value is None or value == "":
    return default
  return value


def get_env_int(name: str, default: int | None = None) -> int | None:
  value = get_env_str(name)
  if value is None:
    return default

  try:
    return int(value)
  except ValueError as exc:
    raise ValueError(f"Environment variable {name} must be an integer") from exc


def get_upload_dir(*parts: str) -> Path:
  configured_dir = Path(os.getenv("UPLOAD_STORAGE_DIR", str(DEFAULT_STORAGE_DIR)))
  base_dir = configured_dir if configured_dir.is_absolute() else BASE_DIR / configured_dir
  return base_dir.joinpath(*parts)


def read_db_config() -> dict:
  missing = [
    name
    for name in ("DB_NAME", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_PORT")
    if get_env_str(name) is None
  ]

  if missing:
    raise ValueError(
      "Missing database environment variables: " + ", ".join(missing)
    )

  return {
    "db_name": get_env_str("DB_NAME"),
    "host": get_env_str("DB_HOST"),
    "user": get_env_str("DB_USER"),
    "password": get_env_str("DB_PASSWORD"),
    "port": get_env_int("DB_PORT"),
  }


def build_mysql_dsn(config: dict) -> str:
  user = quote(str(config["user"]), safe="")
  password = quote(str(config["password"]), safe="")
  return (
    f"mysql://{user}:{password}"
    f"@{config['host']}:{config['port']}/{config['db_name']}"
  )
