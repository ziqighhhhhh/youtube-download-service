from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from config import DEBUG, SECRET_KEY, STATIC_DIR, TEMPLATES_DIR, DATA_DIR, USERS_DIR
from database import get_db
from services.csrf_service import ensure_csrf_token
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    from database import init_db, SessionLocal
    from config import ADMIN_EMAIL, ADMIN_PASSWORD
    from models.user import User

    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == ADMIN_EMAIL).first():
            admin = User(email=ADMIN_EMAIL, balance=0)
            admin.set_password(ADMIN_PASSWORD)
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="YouTube Batch Downloader", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="strict",
    https_only=not DEBUG,
    max_age=60 * 60 * 24 * 7,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

from routes import auth, tasks, billing, admin, cookie

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(cookie.router)


def _need_login(request: Request) -> bool:
    return not request.session.get("user_id")


def _template(request: Request, name: str, context: dict | None = None):
    ensure_csrf_token(request)
    payload = {"request": request}
    if context:
        payload.update(context)
    return templates.TemplateResponse(request, name, payload)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return _template(request, "dashboard.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/")
    return _template(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/")
    return _template(request, "register.html")


@app.get("/task/{tid}", response_class=HTMLResponse)
async def task_page(tid: int, request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return _template(request, "task_detail.html", {"task_id": tid})


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return _template(request, "history.html")


@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return _template(request, "account.html")


@app.get("/bookmarklet", response_class=HTMLResponse)
async def bookmarklet_page(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return _template(request, "bookmarklet.html")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    if _need_login(request):
        return RedirectResponse(url="/login")
    from routes.admin import check_admin

    check_admin(request, db)
    return _template(request, "admin.html")
