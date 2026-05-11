from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class CookieSubmit(BaseModel):
    cookie_text: str


class TaskSubmit(BaseModel):
    url: str


class RechargeRequest(BaseModel):
    amount: float
    note: str = ""
