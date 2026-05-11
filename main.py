from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from config import SECRET_KEY, STATIC_DIR, TEMPLATES_DIR, DATA_DIR, USERS_DIR

app = FastAPI(title="YouTube Batch Downloader")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.on_event("startup")
async def startup():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    from database import init_db

    init_db()
    from config import ADMIN_EMAIL, ADMIN_PASSWORD
    from database import SessionLocal
    from models.user import User

    db = SessionLocal()
    if not db.query(User).filter(User.email == ADMIN_EMAIL).first():
        a = User(email=ADMIN_EMAIL, balance=0)
        a.set_password(ADMIN_PASSWORD)
        db.add(a)
        db.commit()
    db.close()


from routes import auth, tasks, billing, admin, cookie

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(cookie.router)


def _need_login(request: Request) -> bool:
    return not request.session.get("user_id")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/task/{tid}", response_class=HTMLResponse)
async def task_page(tid: int, request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        "task_detail.html", {"request": request, "task_id": tid}
    )


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("account.html", {"request": request})


@app.get("/bookmarklet", response_class=HTMLResponse)
async def bookmarklet_page(request: Request):
    if _need_login(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("bookmarklet.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
