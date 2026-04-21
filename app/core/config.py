import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_FILE = BASE_DIR / "koneksi_config.txt"
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


def get_upload_dir(*parts: str) -> Path:
  configured_dir = Path(os.getenv("UPLOAD_STORAGE_DIR", str(DEFAULT_STORAGE_DIR)))
  base_dir = configured_dir if configured_dir.is_absolute() else BASE_DIR / configured_dir
  return base_dir.joinpath(*parts)


def read_db_config(config_path: Path = DEFAULT_CONFIG_FILE) -> dict:
  if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")

  lines = config_path.read_text(encoding="utf-8").splitlines()
  if not lines:
    raise ValueError(f"Config file is empty: {config_path}")

  line = lines[0].strip()
  parts = [part.strip() for part in line.split(",")]

  if len(parts) != 5:
    raise ValueError(
      f"Invalid config format in {config_path}. Expected 5 values: db,host,user,password,port"
    )

  db_name, host, user, password, port = parts
  return {
    "db_name": db_name,
    "host": host,
    "user": user,
    "password": password,
    "port": int(port),
  }


def build_mysql_dsn(config: dict) -> str:
  return (
    f"mysql://{config['user']}:{config['password']}"
    f"@{config['host']}:{config['port']}/{config['db_name']}"
  )
