from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


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
