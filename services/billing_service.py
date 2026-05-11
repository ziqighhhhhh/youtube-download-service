import math
from sqlalchemy.orm import Session
from models.user import User
from models.billing import BillingRecord
from config import VIDEOS_PER_CHARGE


def calculate_cost(video_count: int) -> float:
    return math.ceil(video_count / VIDEOS_PER_CHARGE)


def deduct_balance(db: Session, user_id: int, cost: float, desc: str = "") -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.balance < cost:
        return False
    user.balance -= cost
    db.add(
        BillingRecord(
            user_id=user_id,
            action="charge",
            amount=-cost,
            balance_after=user.balance,
            description=desc,
        )
    )
    db.commit()
    return True


def add_balance(
    db: Session, user_id: int, amount: float, desc: str = "管理员充值"
) -> float:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    user.balance += amount
    db.add(
        BillingRecord(
            user_id=user_id,
            action="refill",
            amount=amount,
            balance_after=user.balance,
            description=desc,
        )
    )
    db.commit()
    return user.balance


def get_balance(db: Session, user_id: int) -> float:
    user = db.query(User).filter(User.id == user_id).first()
    return user.balance if user else 0.0
