from __future__ import annotations

import asyncio
from collections.abc import Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class BotScheduler:
    def __init__(self, timezone: str = "Europe/Moscow"):
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self._lock = asyncio.Lock()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def reschedule(self, times: list[str], job_func: Callable[[], Awaitable[None]]) -> None:
        self.scheduler.remove_all_jobs()
        for item in times:
            if not item or ":" not in item:
                continue
            hour, minute = item.split(":", 1)
            trigger = CronTrigger(hour=int(hour), minute=int(minute), timezone=self.timezone)
            self.scheduler.add_job(lambda jf=job_func: asyncio.create_task(self._run_locked(jf)), trigger=trigger, id=f"autopost_{hour}_{minute}", replace_existing=True, misfire_grace_time=180)

    async def _run_locked(self, job_func: Callable[[], Awaitable[None]]) -> None:
        if self._lock.locked():
            return
        async with self._lock:
            await job_func()

    def next_runs(self) -> list[str]:
        out=[]
        for job in self.scheduler.get_jobs():
            out.append(f"{job.id}: {job.next_run_time}")
        return out
