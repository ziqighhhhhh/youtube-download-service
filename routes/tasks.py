import asyncio
from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session
from database import get_db
from models.task import Task
from services import cookie_service, billing_service
from services.ytdlp_manager import YtDlpManager
from services.queue_manager import get_queue_manager
from schemas.all import TaskSubmit

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/")
async def create(data: TaskSubmit, request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    if not cookie_service.has_cookie(uid):
        raise HTTPException(400, "请先提交 Cookie")

    cp = str(cookie_service.get_user_cookie_path(uid))
    mgr = YtDlpManager()
    try:
        vc = await mgr.get_video_count(data.url)
    except Exception as e:
        raise HTTPException(500, f"预扫描失败: {e}")

    cost = billing_service.calculate_cost(vc)
    bal = billing_service.get_balance(db, uid)
    if bal < cost:
        raise HTTPException(400, f"余额不足: 需要 {cost} 次, 当前 {bal}")

    if not billing_service.deduct_balance(db, uid, cost, f"预扣: {vc} 个视频"):
        raise HTTPException(500, "扣费失败")

    task = Task(
        user_id=uid,
        youtube_url=data.url,
        status="downloading",
        video_count_total=vc,
        cost=cost,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    qm = get_queue_manager()

    async def run():
        y = YtDlpManager()
        try:
            async for line in y.download_stream(data.url, cp):
                await qm.broadcast_progress(task.id, line)
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
            return
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        db.commit()

    qm.active_tasks[task.id] = asyncio.create_task(run())
    return {"task_id": task.id, "message": "已提交"}


@router.get("/")
async def list_tasks(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    return (
        db.query(Task)
        .filter(Task.user_id == uid)
        .order_by(Task.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/{tid}")
async def get_task(tid: int, request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "未登录")
    t = db.query(Task).filter(Task.id == tid, Task.user_id == uid).first()
    if not t:
        raise HTTPException(404, "不存在")
    return t


@router.websocket("/ws/{tid}")
async def ws(websocket: WebSocket, tid: int):
    await websocket.accept()
    qm = get_queue_manager()

    async def h(m):
        try:
            await websocket.send_text(m)
        except:
            pass

    qm.register_progress_handler(tid, h)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
