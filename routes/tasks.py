import asyncio
from datetime import UTC, datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models.task import Task
from services import cookie_service, billing_service
from services.csrf_service import require_csrf
from services.ytdlp_manager import YtDlpManager
from services.queue_manager import get_queue_manager
from schemas.all import TaskSubmit
from config import MAX_CONCURRENT_TASKS

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _parse_done_line(line: str) -> tuple[int, int] | None:
    if not line.startswith("__DONE__:"):
        return None
    parts = line.split(":")
    if len(parts) != 3:
        return None
    try:
        return int(parts[1]), int(parts[2])
    except ValueError:
        return None


@router.post("/")
async def create(data: TaskSubmit, request: Request, db: Session = Depends(get_db)):
    require_csrf(request)
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "Not logged in")
    cookie_text = cookie_service.load_cookie(uid) if cookie_service.has_cookie(uid) else None
    url = str(data.url)
    manager = YtDlpManager()
    try:
        video_count = await manager.get_video_count(url, cookie_text)
    except Exception as exc:
        if cookie_text:
            try:
                video_count = await manager.get_video_count(url)
            except Exception:
                raise HTTPException(500, f"Pre-scan failed: {exc}") from exc
        else:
            raise HTTPException(500, f"Pre-scan failed: {exc}") from exc

    cost = billing_service.calculate_cost(video_count)
    task = billing_service.create_charged_task(
        db,
        uid,
        url,
        video_count,
        cost,
        f"Pre-charge: {video_count} videos",
    )
    if not task:
        balance = billing_service.get_balance(db, uid)
        raise HTTPException(400, f"Insufficient balance: need {cost}, current {balance}")

    queue = get_queue_manager(MAX_CONCURRENT_TASKS)

    async def run():
        task_db = SessionLocal()
        ok = 0
        fail = 0
        try:
            downloader = YtDlpManager()
            async for line in downloader.download_stream(url, cookie_text):
                await queue.broadcast_progress(task.id, line)
                parsed = _parse_done_line(line)
                if parsed:
                    ok, fail = parsed

            task_row = task_db.query(Task).filter(Task.id == task.id).first()
            if not task_row:
                return
            task_row.video_count_success = ok
            task_row.video_count_failed = fail
            task_row.completed_at = datetime.now(UTC)
            if ok == 0 and fail > 0:
                task_row.status = "failed"
                task_row.error_message = "All downloads failed"
                task_db.commit()
                billing_service.refund_balance(
                    task_db,
                    uid,
                    cost,
                    f"Refund failed task {task.id}",
                )
            else:
                task_row.status = "completed"
                task_db.commit()
        except Exception as exc:
            task_db.rollback()
            task_row = task_db.query(Task).filter(Task.id == task.id).first()
            if task_row:
                task_row.status = "failed"
                task_row.error_message = str(exc)
                task_row.completed_at = datetime.now(UTC)
                task_db.commit()
            raise
        finally:
            task_db.close()

    queue.active_tasks[task.id] = asyncio.create_task(queue.enqueue(task.id, run))
    return {"task_id": task.id, "message": "Submitted"}


@router.get("/")
async def list_tasks(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "Not logged in")
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
        raise HTTPException(401, "Not logged in")
    task = db.query(Task).filter(Task.id == tid, Task.user_id == uid).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.websocket("/ws/{tid}")
async def ws(websocket: WebSocket, tid: int, db: Session = Depends(get_db)):
    uid = websocket.session.get("user_id")
    if not uid:
        await websocket.close(code=1008)
        return
    task = db.query(Task).filter(Task.id == tid, Task.user_id == uid).first()
    if not task:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    queue = get_queue_manager(MAX_CONCURRENT_TASKS)

    async def handler(message):
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    queue.register_progress_handler(tid, handler)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
