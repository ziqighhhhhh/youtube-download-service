from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from database import Base
from datetime import UTC, datetime
from config import DEFAULT_BALANCE
import bcrypt


def utc_now():
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    balance = Column(Float, default=DEFAULT_BALANCE)
    cookie_text = Column(Text, nullable=True)
    cookie_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    is_active = Column(Integer, default=1)

    def __init__(self, **kwargs):
        kwargs.setdefault("balance", DEFAULT_BALANCE)
        kwargs.setdefault("is_active", 1)
        super().__init__(**kwargs)

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )
