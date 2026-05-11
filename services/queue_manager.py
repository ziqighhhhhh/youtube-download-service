import asyncio
from typing import Dict, Optional, Callable


class QueueManager:
    def __init__(self, max_concurrent: int = 3):
        self.active_tasks: Dict[int, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.progress_handlers: Dict[int, list] = {}

    async def enqueue(
        self, task_id: int, coro, handler: Optional[Callable] = None
    ):
        if handler:
            self.progress_handlers[task_id] = [handler]
        async with self.semaphore:
            try:
                await coro()
            except Exception as e:
                print(f"Task {task_id} failed: {e}")
            finally:
                self.active_tasks.pop(task_id, None)
                self.progress_handlers.pop(task_id, None)

    def register_progress_handler(self, task_id: int, handler: Callable):
        self.progress_handlers.setdefault(task_id, []).append(handler)

    async def broadcast_progress(self, task_id: int, message: str):
        for h in self.progress_handlers.get(task_id, []):
            try:
                await h(message)
            except:
                pass


_queue = None


def get_queue_manager(max_concurrent: int = 3) -> QueueManager:
    global _queue
    if _queue is None:
        _queue = QueueManager(max_concurrent)
    return _queue
