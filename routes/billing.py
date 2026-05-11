from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services import billing_service
from models.billing import BillingRecord
from schemas.all import RechargeRequest

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/balance")
async def balance(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    return {"balance": billing_service.get_balance(db, uid)}


@router.post("/recharge-request")
async def recharge(
    data: RechargeRequest, request: Request, db: Session = Depends(get_db)
):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    db.add(
        BillingRecord(
            user_id=uid,
            action="recharge_request",
            amount=data.amount,
            balance_after=billing_service.get_balance(db, uid),
            description=f"申请: {data.note}",
        )
    )
    db.commit()
    return {"message": "已提交"}
