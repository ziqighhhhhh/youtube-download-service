import asyncio

from fastapi import HTTPException

from routes import tasks


class DummyRequest:
    def __init__(self, user_id=1):
        self.session = {"user_id": user_id, "csrf_token": "token"}
        self.headers = {"x-csrf-token": "token"}


class DummyDb:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)
        item.id = 123

    def commit(self):
        return None

    def refresh(self, item):
        return None


class DummyManager:
    async def get_video_count(self, url):
        return 1

    async def download_stream(self, url, cookies_file):
        yield "__DONE__:1:0"


class DummyQueue:
    def __init__(self):
        self.active_tasks = {}
        self.enqueued = []

    async def broadcast_progress(self, task_id, message):
        return None

    async def enqueue(self, task_id, coro, handler=None):
        self.enqueued.append((task_id, coro))


def test_create_uses_queue_manager_enqueue(monkeypatch):
    queue = DummyQueue()

    monkeypatch.setattr(tasks.cookie_service, "has_cookie", lambda uid: True)
    monkeypatch.setattr(tasks.cookie_service, "get_user_cookie_path", lambda uid: "cookies.txt")
    monkeypatch.setattr(tasks, "YtDlpManager", DummyManager)
    def create_charged_task(db, uid, url, video_count, cost, desc):
        task = tasks.Task(user_id=uid, youtube_url=url, video_count_total=video_count, cost=cost)
        task.id = 123
        return task

    monkeypatch.setattr(tasks.billing_service, "calculate_cost", lambda count: 1)
    monkeypatch.setattr(tasks.billing_service, "create_charged_task", create_charged_task)
    monkeypatch.setattr(tasks, "get_queue_manager", lambda max_concurrent=3: queue)

    result = asyncio.run(
        tasks.create(
            tasks.TaskSubmit(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            DummyRequest(),
            DummyDb(),
        )
    )

    assert result["task_id"] == 123
    assert queue.enqueued
    assert queue.active_tasks[123]


def test_parse_done_line():
    assert tasks._parse_done_line("__DONE__:2:1") == (2, 1)
    assert tasks._parse_done_line("other") is None


def test_websocket_rejects_unauthenticated(monkeypatch):
    class WebSocket:
        session = {}

        async def close(self, code):
            self.code = code

    socket = WebSocket()

    asyncio.run(tasks.ws(socket, 1, db=object()))

    assert socket.code == 1008
