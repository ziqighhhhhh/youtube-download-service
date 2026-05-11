from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User
from config import USERS_DIR


def get_user_cookie_path(user_id: int) -> Path:
    p = USERS_DIR / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p / "cookies.txt"


def save_cookie(db: Session, user_id: int, text: str) -> bool:
    try:
        get_user_cookie_path(user_id).write_text(text, encoding="utf-8")
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.cookie_text = text
            user.cookie_updated_at = datetime.utcnow()
            db.commit()
        return True
    except Exception as e:
        print(f"Save cookie failed: {e}")
        return False


def load_cookie(user_id: int) -> str:
    p = get_user_cookie_path(user_id)
    return p.read_text(encoding="utf-8") if p.exists() else ""


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
        print(f"Delete cookie failed: {e}")
        return False
