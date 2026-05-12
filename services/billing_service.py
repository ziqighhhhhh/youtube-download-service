import math
from sqlalchemy import update
from sqlalchemy.orm import Session
from models.task import Task
from models.user import User
from models.billing import BillingRecord
from config import VIDEOS_PER_CHARGE


def calculate_cost(video_count: int) -> float:
    return math.ceil(video_count / VIDEOS_PER_CHARGE)


def deduct_balance(db: Session, user_id: int, cost: float, desc: str = "") -> bool:
    if cost <= 0:
        return False
    result = db.execute(
        update(User)
        .where(User.id == user_id, User.balance >= cost)
        .values(balance=User.balance - cost)
    )
    if result.rowcount != 1:
        db.rollback()
        return False
    user = db.query(User).filter(User.id == user_id).first()
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


def create_charged_task(
    db: Session,
    user_id: int,
    youtube_url: str,
    video_count: int,
    cost: float,
    desc: str = "",
) -> Task | None:
    if cost <= 0:
        return None
    try:
        result = db.execute(
            update(User)
            .where(User.id == user_id, User.balance >= cost)
            .values(balance=User.balance - cost)
        )
        if result.rowcount != 1:
            db.rollback()
            return None

        user = db.query(User).filter(User.id == user_id).first()
        task = Task(
            user_id=user_id,
            youtube_url=youtube_url,
            status="downloading",
            video_count_total=video_count,
            cost=cost,
        )
        db.add(task)
        db.flush()
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
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def refund_balance(db: Session, user_id: int, amount: float, desc: str = "") -> float:
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    user.balance += amount
    db.add(
        BillingRecord(
            user_id=user_id,
            action="refund",
            amount=amount,
            balance_after=user.balance,
            description=desc,
        )
    )
    db.commit()
    return user.balance


def add_balance(
    db: Session, user_id: int, amount: float, desc: str = "Admin recharge"
) -> float:
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
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
