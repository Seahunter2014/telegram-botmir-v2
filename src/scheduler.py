import logging
from collections.abc import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger(__name__)

class NewsroomScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
        self.job_ids: list[str] = []

    def start(self):
        """
        Start only inside an already running asyncio event loop.
        PTB creates the loop during Application.run_polling(), so this must be
        called from Application.post_init, not before run_polling().
        """
        if not self.scheduler.running:
            self.scheduler.start()
            log.info("Newsroom scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            log.info("Newsroom scheduler stopped")

    def reschedule(self, times: list[str], callback: Callable[[], object]):
        for job_id in list(self.job_ids):
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
        self.job_ids = []

        for idx, t in enumerate(times):
            try:
                hour, minute = [int(x) for x in t.split(":")]
                job = self.scheduler.add_job(
                    callback,
                    "cron",
                    hour=hour,
                    minute=minute,
                    id=f"autopost_{idx}_{hour:02d}_{minute:02d}",
                    replace_existing=True,
                    misfire_grace_time=300,
                    coalesce=True,
                    max_instances=1,
                )
                self.job_ids.append(job.id)
            except Exception as exc:
                log.warning("bad schedule time %s: %s", t, exc)
