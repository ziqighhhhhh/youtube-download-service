import secrets
from fastapi import HTTPException, Request

CSRF_SESSION_KEY = "csrf_token"
CSRF_HEADER = "x-csrf-token"


def ensure_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


def require_csrf(request: Request) -> None:
    expected = request.session.get(CSRF_SESSION_KEY)
    supplied = request.headers.get(CSRF_HEADER)
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
