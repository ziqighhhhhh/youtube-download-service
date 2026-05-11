from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.task import Task
from services import billing_service
from config import ADMIN_EMAIL

router = APIRouter(prefix="/api/admin", tags=["admin"])


def check_admin(req: Request, db: Session):
    uid = req.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    u = db.query(User).filter(User.id == uid).first()
    if not u or u.email != ADMIN_EMAIL:
        raise HTTPException(403, "需要管理员权限")
    return u


@router.get("/users")
async def users(req: Request, db: Session = Depends(get_db)):
    check_admin(req, db)
    return db.query(User).all()


@router.post("/users/{uid}/recharge")
async def recharge(uid: int, amount: float, req: Request, db: Session = Depends(get_db)):
    check_admin(req, db)
    if amount <= 0:
        raise HTTPException(400, "充值金额必须大于 0")
    nb = billing_service.add_balance(db, uid, amount)
    return {"message": f"已充值，余额: {nb}"}


@router.get("/tasks")
async def tasks(req: Request, db: Session = Depends(get_db)):
    check_admin(req, db)
    return db.query(Task).order_by(Task.created_at.desc()).limit(100).all()
