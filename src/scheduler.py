from __future__ import annotations

from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .newsroom import create_package
from .publisher import publish_to_channel
from .state_store import load_state, remember_publication, record_skip, save_state


async def autopost_job(application: Any, slot: str) -> None:
    state = load_state()
    if not state.get("autopost_enabled"):
        return
    bundle = application.bot_data["bundle"]
    channel = application.bot_data.get("channel_id", "")
    if not channel:
        record_skip("no_channel_id", "Не задан TELEGRAM_CHANNEL_ID")
        return
    try:
        package = create_package(bundle, forced_slot=slot, require_minimum_quality=True)
        variant = package["best_variant"]
        used = await publish_to_channel(application.bot, channel, variant, package["media"], package["plan"], package["signal"])
        remember_publication(package, variant, "autopost", used)
    except Exception as exc:
        record_skip("autopost_failed", str(exc), {"slot": slot})


def build_scheduler(application: Any) -> AsyncIOScheduler:
    old = application.bot_data.get("scheduler")
    if old:
        try:
            old.shutdown(wait=False)
        except Exception:
            pass
    bundle = application.bot_data["bundle"]
    scheduler = AsyncIOScheduler(timezone=bundle.policy.get("timezone", "Europe/Moscow"))
    times = load_state().get("post_times") or bundle.policy.get("default_post_times", ["09:00", "14:00", "19:00"])
    slots = ["morning", "day", "evening"]
    for index, time_value in enumerate(times):
        try:
            hour, minute = [int(value) for value in time_value.split(":")]
        except Exception:
            continue
        scheduler.add_job(
            autopost_job,
            CronTrigger(hour=hour, minute=minute),
            args=[application, slots[index] if index < 3 else "day"],
            id=f"autopost_{index}",
            replace_existing=True,
        )
    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    return scheduler


def set_autopost(enabled: bool) -> None:
    state = load_state()
    state["autopost_enabled"] = enabled
    save_state(state)


def set_schedule(times: list[str]) -> None:
    state = load_state()
    state["post_times"] = times
    save_state(state)
