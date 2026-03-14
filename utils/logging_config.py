import logging
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "storage" / "logs"


class MaxLevelFilter(logging.Filter):
  def __init__(self, max_level: int):
    super().__init__()
    self.max_level = max_level

  def filter(self, record: logging.LogRecord) -> bool:
    return record.levelno <= self.max_level


def ensure_log_dir() -> Path:
  LOG_DIR.mkdir(parents=True, exist_ok=True)
  return LOG_DIR


def _build_formatter() -> logging.Formatter:
  return logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
  )


def get_logger(
  name: str,
  filename: str,
  level: int = logging.INFO,
  include_console: bool = True,
) -> logging.Logger:
  ensure_log_dir()
  logger = logging.getLogger(name)
  logger.setLevel(level)
  logger.propagate = False

  target_path = str(LOG_DIR / filename)
  formatter = _build_formatter()

  has_file_handler = any(
    isinstance(handler, logging.FileHandler)
    and Path(getattr(handler, "baseFilename", "")) == Path(target_path)
    for handler in logger.handlers
  )
  if not has_file_handler:
    file_handler = logging.FileHandler(target_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

  has_console_handler = any(
    isinstance(handler, logging.StreamHandler)
    and not isinstance(handler, logging.FileHandler)
    for handler in logger.handlers
  )
  if include_console and not has_console_handler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

  return logger


def configure_uvicorn_logging() -> None:
  ensure_log_dir()
  formatter = _build_formatter()
  uvicorn_error_logger = logging.getLogger("uvicorn.error")
  uvicorn_error_logger.setLevel(logging.INFO)

  app_log_path = str(LOG_DIR / "app.log")
  has_app_file_handler = any(
    isinstance(handler, logging.FileHandler)
    and Path(getattr(handler, "baseFilename", "")) == Path(app_log_path)
    for handler in uvicorn_error_logger.handlers
  )
  if not has_app_file_handler:
    app_file_handler = logging.FileHandler(app_log_path, encoding="utf-8")
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.addFilter(MaxLevelFilter(logging.WARNING))
    app_file_handler.setFormatter(formatter)
    uvicorn_error_logger.addHandler(app_file_handler)

  error_log_path = str(LOG_DIR / "error.log")
  has_error_file_handler = any(
    isinstance(handler, logging.FileHandler)
    and Path(getattr(handler, "baseFilename", "")) == Path(error_log_path)
    for handler in uvicorn_error_logger.handlers
  )
  if not has_error_file_handler:
    error_file_handler = logging.FileHandler(error_log_path, encoding="utf-8")
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    uvicorn_error_logger.addHandler(error_file_handler)

  uvicorn_access_logger = logging.getLogger("uvicorn.access")
  uvicorn_access_logger.setLevel(logging.INFO)

  has_access_file_handler = any(
    isinstance(handler, logging.FileHandler)
    and Path(getattr(handler, "baseFilename", "")) == Path(app_log_path)
    for handler in uvicorn_access_logger.handlers
  )
  if not has_access_file_handler:
    access_file_handler = logging.FileHandler(app_log_path, encoding="utf-8")
    access_file_handler.setLevel(logging.INFO)
    access_file_handler.setFormatter(formatter)
    uvicorn_access_logger.addHandler(access_file_handler)


app_logger = get_logger("backend.app", "app.log")
error_logger = get_logger("backend.error", "error.log", level=logging.ERROR)
