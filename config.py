import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

APP_NAME = os.getenv("APP_NAME", "YouTube Batch Downloader")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/app.db")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
VIDEOS_PER_CHARGE = int(os.getenv("VIDEOS_PER_CHARGE", "10"))
DEFAULT_BALANCE = float(os.getenv("DEFAULT_BALANCE", "0"))
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))


def _require_positive_int(name: str, value: int) -> int:
    if value < 1:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


def _validate_security_config() -> None:
    _require_positive_int("VIDEOS_PER_CHARGE", VIDEOS_PER_CHARGE)
    _require_positive_int("MAX_CONCURRENT_TASKS", MAX_CONCURRENT_TASKS)

    if DEBUG:
        return

    if SECRET_KEY == "dev-secret-key-change-me" or len(SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must be set to a strong value in production")
    if ADMIN_PASSWORD == "admin123" or len(ADMIN_PASSWORD) < 12:
        raise RuntimeError("ADMIN_PASSWORD must be set to a strong value in production")


_validate_security_config()
