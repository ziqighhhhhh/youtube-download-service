from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.all import UserRegister, UserLogin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "邮箱已被注册")
    u = User(email=data.email, balance=0)
    u.set_password(data.password)
    db.add(u)
    db.commit()
    return {"message": "注册成功"}


@router.post("/login")
async def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == data.email).first()
    if not u or not u.check_password(data.password):
        raise HTTPException(401, "邮箱或密码错误")
    if not u.is_active:
        raise HTTPException(403, "账户已被禁用")
    request.session["user_id"] = u.id
    return {"message": "登录成功"}


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "已登出"}


@router.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(404, "不存在")
    return {
        "id": u.id,
        "email": u.email,
        "balance": u.balance,
        "cookie_updated_at": u.cookie_updated_at,
        "created_at": u.created_at,
    }
