import asyncio
from asyncio import Task
from typing import Optional

from app.store import Store

QUEUES = {}


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def worker(self, queue):
        while True:
            update = await queue.get()
            await self.store.bots_manager.handle_update(update)
            queue.task_done()

    async def stop(self):
        self.is_running = False
        await self.poll_task

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            for update in updates:
                chat_id = update.object.peer_id
                if QUEUES.get(chat_id) is None:
                    QUEUES[chat_id] = asyncio.Queue()
                    asyncio.create_task(self.worker(QUEUES[chat_id]))
                QUEUES[chat_id].put_nowait(update)
