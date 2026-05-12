from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from services import cookie_service
from services.csrf_service import require_csrf
from schemas.all import CookieSubmit

router = APIRouter(prefix="/api/cookie", tags=["cookie"])


@router.post("/")
async def submit(data: CookieSubmit, request: Request, db: Session = Depends(get_db)):
    require_csrf(request)
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    if not cookie_service.save_cookie(db, uid, data.cookie_text):
        raise HTTPException(500, "保存失败")
    return {"message": "Cookie 已保存"}


@router.get("/status")
async def status(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    u = db.query(User).filter(User.id == uid).first()
    return {
        "exists": cookie_service.has_cookie(uid),
        "updated_at": u.cookie_updated_at if u else None,
    }
