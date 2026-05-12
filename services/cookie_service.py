from pathlib import Path
from datetime import UTC, datetime
import base64
import hashlib
import logging
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session
from models.user import User
from config import SECRET_KEY, USERS_DIR

logger = logging.getLogger(__name__)


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode("utf-8")).digest())
    return Fernet(key)


def get_user_cookie_path(user_id: int) -> Path:
    p = USERS_DIR / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p / "cookies.txt"


def save_cookie(db: Session, user_id: int, text: str) -> bool:
    try:
        encrypted = _fernet().encrypt(text.encode("utf-8"))
        get_user_cookie_path(user_id).write_bytes(encrypted)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.cookie_text = None
            user.cookie_updated_at = datetime.now(UTC)
            db.commit()
        return True
    except Exception as e:
        logger.exception("Save cookie failed for user_id=%s", user_id)
        return False


def load_cookie(user_id: int) -> str:
    p = get_user_cookie_path(user_id)
    if not p.exists():
        return ""
    content = p.read_bytes()
    try:
        return _fernet().decrypt(content).decode("utf-8")
    except InvalidToken:
        logger.warning("Cookie file for user_id=%s is not encrypted", user_id)
        return content.decode("utf-8")


def has_cookie(user_id: int) -> bool:
    return get_user_cookie_path(user_id).exists()


def delete_cookie(db: Session, user_id: int) -> bool:
    try:
        p = get_user_cookie_path(user_id)
        if p.exists():
            p.unlink()
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.cookie_text = None
            user.cookie_updated_at = None
            db.commit()
        return True
    except Exception as e:
        logger.exception("Delete cookie failed for user_id=%s", user_id)
        return False
