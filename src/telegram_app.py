from __future__ import annotations

import asyncio
import html
import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from .config_loader import load_settings, required_env_missing
from .menu import main_menu
from .models import Brief, Button, MediaAsset, PreparedPost, PostVariant, Signal
from .pipeline import EditorialPipeline
from .scheduler import BotScheduler
from .source_health import SourceHealthStore
from .state_store import StateStore
from .telegram_post_writer import TelegramPostWriter
from .version import PROJECT_NAME, VERSION

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mir-na-ladoni")
settings = load_settings()
state = StateStore()
scheduler = BotScheduler(settings.schedule_timezone)
source_health = SourceHealthStore()


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and str(user.id) == str(settings.telegram_admin_id))


async def admin_only(update: Update) -> bool:
    if is_admin(update):
        return True
    if update.effective_message:
        await update.effective_message.reply_text("Команда доступна только администратору.")
    return False


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await update.message.reply_text(
        f"{PROJECT_NAME}\n\nВерсия: {VERSION}\n\nГлавные команды: /test, /run_once, /status, /schedule, /channels",
        reply_markup=main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start_cmd(update, context)


async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await update.message.reply_text(VERSION)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load()
    channels = state.channels(settings.telegram_channel_id)
    next_runs = scheduler.next_runs()
    last = data.get("last_run") or {}
    text = [
        "📊 Статус бота",
        f"Версия: {VERSION}",
        f"Автопостинг: {'включён' if data.get('autopost_enabled') else 'выключен'}",
        f"Расписание: {', '.join(data.get('schedule_times', []))}",
        f"Таймзона: {settings.schedule_timezone}",
        f"Следующий запуск: {next_runs[0] if next_runs else 'не запланирован'}",
        f"Каналы: {', '.join(channels) if channels else 'не заданы'}",
        f"Последний результат: {data.get('last_result') or 'нет'}",
    ]
    if last:
        text.append(f"Последний запуск: {last.get('started_at')} → {last.get('result')}")
        if last.get("message"):
            text.append(f"Сообщение: {last.get('message')}")
    await update.message.reply_text("\n".join(text))


async def sources_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await update.message.reply_text(source_health.summary_text()[:3900])


async def services_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    from .config_loader import CONFIG_DIR, load_json
    services = load_json(CONFIG_DIR / "services.json", default=[])
    lines=["🔗 Сервисы:"]
    for s in services:
        if s.get("status") == "active":
            lines.append(f"• {s.get('key')} — {s.get('category')}")
    await update.message.reply_text("\n".join(lines[:80]))


async def topics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    from .config_loader import CONFIG_DIR, load_json
    topics = load_json(CONFIG_DIR / "fallback_topics.json", default=[])
    cats={}
    for t in topics:
        cats[t.get("category", "other")] = cats.get(t.get("category", "other"), 0) + 1
    await update.message.reply_text("🧭 Fallback-темы:\n" + "\n".join(f"• {k}: {v}" for k,v in cats.items()))


async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load()
    await update.message.reply_text(f"Расписание: {', '.join(data.get('schedule_times', []))}\nИзменить: /schedule_set 09:00,14:00,19:00")


async def schedule_set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    raw = " ".join(context.args).strip()
    if not raw:
        await update.message.reply_text("Укажите время: /schedule_set 09:00,14:00,19:00")
        return
    times = [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]
    valid=[]
    for t in times:
        try:
            h,m=t.split(":")
            assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
            valid.append(f"{int(h):02d}:{int(m):02d}")
        except Exception:
            await update.message.reply_text(f"Некорректное время: {t}")
            return
    data=state.load(); data["schedule_times"]=valid; state.save(data)
    scheduler.reschedule(valid, lambda: scheduled_autopost(context.application))
    await update.message.reply_text(f"Расписание обновлено: {', '.join(valid)}")


async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    channels = state.channels(settings.telegram_channel_id)
    await update.message.reply_text("Каналы публикации:\n" + ("\n".join(f"• {c}" for c in channels) or "не заданы"))


async def add_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    if not context.args:
        await update.message.reply_text("Укажите канал: /add_channel @channel")
        return
    data=state.load(); channels=data.get("channels") or []
    for c in context.args:
        if c not in channels:
            channels.append(c)
    data["channels"]=channels; state.save(data)
    await update.message.reply_text("Канал добавлен. /channels")


async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    if not context.args:
        await update.message.reply_text("Укажите канал: /remove_channel @channel")
        return
    data=state.load(); channels=data.get("channels") or []
    channels=[c for c in channels if c not in context.args]
    data["channels"]=channels; state.save(data)
    await update.message.reply_text("Канал удалён. /channels")


async def set_channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    raw=" ".join(context.args)
    channels=[x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]
    data=state.load(); data["channels"]=channels; state.save(data)
    await update.message.reply_text("Каналы обновлены. /channels")


async def autopost_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data=state.load(); data["autopost_enabled"]=True; state.save(data)
    scheduler.reschedule(data.get("schedule_times", ["09:00","14:00","19:00"]), lambda: scheduled_autopost(context.application))
    await update.message.reply_text("Автопостинг включён.")


async def autopost_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data=state.load(); data["autopost_enabled"]=False; state.save(data)
    await update.message.reply_text("Автопостинг выключен.")


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    idx = 0
    if context.args and context.args[0].isdigit():
        idx = int(context.args[0])
    await update.message.reply_text("Ищу тему и готовлю лучший пост через OpenAI…")
    pipeline = EditorialPipeline(settings, bot=context.bot)
    prepared, report = await pipeline.prepare_post(test_index=idx)
    if not prepared:
        await update.message.reply_text(report.admin_text())
        return
    writer = TelegramPostWriter()
    header = (
        f"🧪 Тест темы\n"
        f"Источник: {prepared.signal.source_name}\n"
        f"Жанр: {prepared.brief.genre} · слот: {prepared.brief.slot} · score: {prepared.signal.score}\n"
        f"Угол: {prepared.brief.editorial_angle}\n"
    )
    await update.message.reply_text(header)
    buttons=[]
    for v in prepared.variants[:1]:
        preview = writer.preview(v, prepared.brief)
        await update.message.reply_text(f"Пост · {v.style} · качество {v.score}/100\n\n{preview[:3500]}", parse_mode="HTML", disable_web_page_preview=True)
        buttons.append([InlineKeyboardButton("Опубликовать", callback_data=f"publish:{prepared.session_id}:{v.variant_id}")])
    buttons.append([InlineKeyboardButton("Переписать", callback_data=f"rewrite:{idx+1}"), InlineKeyboardButton("Отклонить", callback_data=f"reject:{prepared.session_id}")])
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(buttons))


async def run_once_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await update.message.reply_text("Запуск начат. Собираю источники, выбираю тему, генерирую пост…")
    pipeline = EditorialPipeline(settings, bot=context.bot)
    prepared, result, report = await pipeline.run_once()
    await update.message.reply_text(report.admin_text()[:3900])


async def why_skipped_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data=state.load(); last=data.get("last_run") or {}
    await update.message.reply_text((last.get("message") or "Последней причины пропуска нет.")[:3900])


async def last_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    pubs=state.publications()
    if not pubs:
        await update.message.reply_text("Публикаций пока нет.")
        return
    p=pubs[-1]
    await update.message.reply_text(f"Последняя публикация:\n{p.get('published_at')}\n{p.get('title')}\n{p.get('genre')} · {p.get('source_name')}")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q=update.callback_query
    await q.answer()
    if not is_admin(update):
        return
    data=q.data or ""
    if data.startswith("publish:"):
        _, session_id, variant_s = data.split(":", 2)
        session=state.get_session(session_id)
        if not session:
            await q.edit_message_text("Сессия не найдена. Запустите /test заново.")
            return
        prepared = prepared_from_dict(session)
        pipeline=EditorialPipeline(settings, bot=context.bot)
        result, report = await pipeline.publish_prepared(prepared, variant_id=int(variant_s))
        await q.edit_message_text(report.admin_text()[:3900])
    elif data.startswith("rewrite:"):
        await q.edit_message_text("Запустите новую генерацию командой /test " + data.split(":",1)[1])
    elif data.startswith("reject:"):
        await q.edit_message_text("Тема отклонена. Запустите /test для новой темы.")


def prepared_from_dict(data: dict[str, Any]) -> PreparedPost:
    signal=Signal(**data["signal"])
    brief=Brief(**data["brief"])
    variants=[PostVariant.from_dict(v) for v in data.get("variants", [])]
    media=MediaAsset(**data.get("media", {}))
    return PreparedPost(session_id=data["session_id"], signal=signal, brief=brief, variants=variants, best_variant_id=data.get("best_variant_id", 1), media=media, diagnostics=data.get("diagnostics", {}))


async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Команда не распознана. Основные команды: /menu, /test, /run_once, /status")


async def scheduled_autopost(app: Application) -> None:
    data = state.load()
    if not data.get("autopost_enabled"):
        return
    pipeline = EditorialPipeline(settings, bot=app.bot)
    prepared, result, report = await pipeline.run_once()
    if report.result != "published" and settings.telegram_admin_id:
        try:
            await app.bot.send_message(chat_id=int(settings.telegram_admin_id), text=report.admin_text()[:3900])
        except Exception:
            log.exception("Не удалось отправить отчёт админу")


async def post_init(app: Application) -> None:
    scheduler.start()
    data = state.load()
    if data.get("autopost_enabled"):
        scheduler.reschedule(data.get("schedule_times", ["09:00","14:00","19:00"]), lambda: scheduled_autopost(app))


async def post_shutdown(app: Application) -> None:
    await scheduler.shutdown()


def build_app() -> Application:
    missing = required_env_missing(settings)
    if missing:
        raise RuntimeError("Не заданы обязательные переменные окружения: " + ", ".join(missing))
    app = Application.builder().token(settings.telegram_bot_token).post_init(post_init).post_shutdown(post_shutdown).build()
    commands = [
        ("start", start_cmd), ("help", help_cmd), ("menu", start_cmd), ("version", version_cmd), ("status", status_cmd),
        ("test", test_cmd), ("run_once", run_once_cmd), ("autopost_on", autopost_on_cmd), ("autopost_off", autopost_off_cmd),
        ("schedule", schedule_cmd), ("schedule_set", schedule_set_cmd), ("channels", channels_cmd), ("add_channel", add_channel_cmd),
        ("remove_channel", remove_channel_cmd), ("set_channels", set_channels_cmd), ("sources", sources_cmd), ("services", services_cmd),
        ("topics", topics_cmd), ("why_skipped", why_skipped_cmd), ("last", last_cmd)
    ]
    for name, func in commands:
        app.add_handler(CommandHandler(name, func))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))
    return app


def main() -> None:
    app = build_app()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
