from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.task import Task
from services import billing_service
from services.csrf_service import require_csrf
from config import ADMIN_EMAIL
from schemas.all import AdminRechargeRequest

router = APIRouter(prefix="/api/admin", tags=["admin"])


def check_admin(req: Request, db: Session):
    uid = req.session.get("user_id")
    if not uid:
        raise HTTPException(401, "Not logged in")
    user = db.query(User).filter(User.id == uid).first()
    if not user or user.email != ADMIN_EMAIL:
        raise HTTPException(403, "Admin access required")
    return user


@router.get("/users")
async def users(req: Request, db: Session = Depends(get_db)):
    check_admin(req, db)
    return db.query(User).all()


@router.post("/users/{uid}/recharge")
async def recharge(
    uid: int,
    data: AdminRechargeRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    require_csrf(req)
    check_admin(req, db)
    balance = billing_service.add_balance(db, uid, data.amount)
    return {"message": f"Recharged. Balance: {balance}"}


@router.get("/tasks")
async def tasks(req: Request, db: Session = Depends(get_db)):
    check_admin(req, db)
    return db.query(Task).order_by(Task.created_at.desc()).limit(100).all()
