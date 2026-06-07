import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger(__name__)

class NewsroomScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
        self.job_ids: list[str] = []

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def reschedule(self, times: list[str], callback):
        for job_id in self.job_ids:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
        self.job_ids = []
        for idx, t in enumerate(times):
            try:
                hour, minute = [int(x) for x in t.split(":")]
                job = self.scheduler.add_job(callback, "cron", hour=hour, minute=minute, id=f"autopost_{idx}_{t}")
                self.job_ids.append(job.id)
            except Exception as exc:
                log.warning("bad schedule time %s: %s", t, exc)
