from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CookieSubmit(BaseModel):
    cookie_text: str = Field(min_length=1, max_length=2_000_000)


class TaskSubmit(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def require_youtube_url(cls, value: HttpUrl) -> HttpUrl:
        host = (value.host or "").lower()
        allowed_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
        if host not in allowed_hosts:
            raise ValueError("Only YouTube URLs are allowed")
        return value


class RechargeRequest(BaseModel):
    amount: float = Field(gt=0, le=1_000_000)
    note: str = Field(default="", max_length=500)


class AdminRechargeRequest(BaseModel):
    amount: float = Field(gt=0, le=1_000_000)


class TaskResponse(BaseModel):
    id: int
    user_id: int
    youtube_url: str
    status: str
    video_count_total: int = 0
    video_count_success: int = 0
    video_count_failed: int = 0
    cost: float = 0.0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    email: str
    balance: float
    cookie_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_active: int = 1

    model_config = {"from_attributes": True}


class UserInfoResponse(BaseModel):
    id: int
    email: str
    balance: float
    cookie_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
