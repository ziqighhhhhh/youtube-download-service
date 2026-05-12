from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.all import UserRegister, UserLogin, UserInfoResponse
from config import DEFAULT_BALANCE
from services.csrf_service import require_csrf

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    require_csrf(request)
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(email=data.email, balance=DEFAULT_BALANCE)
    user.set_password(data.password)
    db.add(user)
    db.commit()
    return {"message": "Registered"}


@router.post("/login")
async def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    require_csrf(request)
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.check_password(data.password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    request.session["user_id"] = user.id
    return {"message": "Logged in"}


@router.post("/logout")
async def logout(request: Request):
    require_csrf(request)
    request.session.clear()
    return {"message": "Logged out"}


@router.get("/me", response_model=UserInfoResponse)
async def me(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "Not logged in")
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
