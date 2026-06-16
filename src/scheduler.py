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
            try:
                hour, minute = item.split(":", 1)
                hour_i = int(hour)
                minute_i = int(minute)
            except Exception:
                continue
            if not (0 <= hour_i <= 23 and 0 <= minute_i <= 59):
                continue
            trigger = CronTrigger(hour=hour_i, minute=minute_i, timezone=self.timezone)
            async def runner(jf=job_func):
                await self._run_locked(jf)

            self.scheduler.add_job(
                runner,
                trigger=trigger,
                id=f"autopost_{hour_i:02d}_{minute_i:02d}",
                replace_existing=True,
                misfire_grace_time=1800,
                coalesce=True,
            )

    async def _run_locked(self, job_func: Callable[[], Awaitable[None]]) -> None:
        if self._lock.locked():
            return
        async with self._lock:
            await job_func()

    def next_runs(self) -> list[str]:
        jobs = sorted(self.scheduler.get_jobs(), key=lambda j: j.next_run_time or 0)
        return [f"{job.id}: {job.next_run_time}" for job in jobs]
