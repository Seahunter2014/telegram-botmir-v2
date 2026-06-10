from __future__ import annotations

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from .config_loader import load_settings, required_env_missing
from .menu import (
    BTN_ADD_CHANNEL,
    BTN_AUTOP_OFF,
    BTN_AUTOP_ON,
    BTN_CHANNELS,
    BTN_LAST,
    BTN_MENU,
    BTN_PUBLISH,
    BTN_SCHEDULE,
    BTN_SET_CHANNELS,
    BTN_SET_SCHEDULE,
    BTN_SOURCES,
    BTN_STATUS,
    BTN_TEST,
    main_menu,
)
from .models import Brief, MediaAsset, PreparedPost, PostVariant, Signal
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


async def send_long(message, text: str, **kwargs) -> None:
    text = text or ""
    limit = 3800
    parts = [text[i:i + limit] for i in range(0, len(text), limit)] or [""]
    for part in parts:
        await message.reply_text(part, **kwargs)


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
    await update.effective_message.reply_text(
        f"{PROJECT_NAME}\n\nВерсия: {VERSION}\n\nУправление — кнопками ниже.",
        reply_markup=main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start_cmd(update, context)


async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await update.effective_message.reply_text(VERSION)


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
    await update.effective_message.reply_text("\n".join(text), reply_markup=main_menu())


async def sources_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await send_long(update.effective_message, source_health.summary_text())


async def services_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    from .config_loader import CONFIG_DIR, load_json
    services = load_json(CONFIG_DIR / "services.json", default=[])
    lines = ["🔗 Сервисы:"]
    for s in services:
        if s.get("status") == "active":
            lines.append(f"• {s.get('key')} — {s.get('category')}")
    await send_long(update.effective_message, "\n".join(lines[:100]))


async def topics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    from .config_loader import CONFIG_DIR, load_json
    topics = load_json(CONFIG_DIR / "fallback_topics.json", default=[])
    cats = {}
    for t in topics:
        cats[t.get("category", "other")] = cats.get(t.get("category", "other"), 0) + 1
    await update.effective_message.reply_text("🧭 Fallback-темы:\n" + "\n".join(f"• {k}: {v}" for k, v in cats.items()))


async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load()
    await update.effective_message.reply_text(
        f"🕒 Расписание: {', '.join(data.get('schedule_times', []))}\n\nДля замены нажмите «{BTN_SET_SCHEDULE}» или отправьте:\n/schedule_set 09:00,14:00,19:00",
        reply_markup=main_menu(),
    )


async def schedule_set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    raw = " ".join(context.args).strip()
    await set_schedule_from_text(update.effective_message, raw, context)


async def set_schedule_from_text(message, raw: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not raw:
        await message.reply_text("Введите расписание в формате: 09:00,14:00,19:00")
        return
    times = [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]
    valid = []
    for t in times:
        try:
            h, m = t.split(":")
            assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
            valid.append(f"{int(h):02d}:{int(m):02d}")
        except Exception:
            await message.reply_text(f"Некорректное время: {t}")
            return
    data = state.load(); data["schedule_times"] = valid; state.save(data)
    scheduler.reschedule(valid, lambda: scheduled_autopost(context.application))
    await message.reply_text(f"Расписание обновлено: {', '.join(valid)}", reply_markup=main_menu())


async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    channels = state.channels(settings.telegram_channel_id)
    await update.effective_message.reply_text(
        "📣 Каналы публикации:\n" + ("\n".join(f"• {c}" for c in channels) or "не заданы"),
        reply_markup=main_menu(),
    )


async def add_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    if not context.args:
        context.user_data["awaiting"] = "add_channel"
        await update.effective_message.reply_text("Введите канал для добавления, например: @NadoTurKrd")
        return
    await add_channels_from_text(update.effective_message, " ".join(context.args))


async def add_channels_from_text(message, raw: str) -> None:
    channels_to_add = [x.strip() for x in raw.replace(";", ",").replace(" ", ",").split(",") if x.strip()]
    data = state.load(); channels = data.get("channels") or []
    if isinstance(channels, str):
        channels = [channels]
    for c in channels_to_add:
        if c not in channels:
            channels.append(c)
    data["channels"] = channels; state.save(data)
    await message.reply_text("Канал добавлен.\n" + "\n".join(f"• {c}" for c in channels), reply_markup=main_menu())


async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Укажите канал: /remove_channel @channel")
        return
    data = state.load(); channels = data.get("channels") or []
    channels = [c for c in channels if c not in context.args]
    data["channels"] = channels; state.save(data)
    await update.effective_message.reply_text("Канал удалён. /channels", reply_markup=main_menu())


async def set_channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    raw = " ".join(context.args)
    if not raw:
        context.user_data["awaiting"] = "set_channels"
        await update.effective_message.reply_text("Введите новый список каналов через запятую, например: @test,@NadoTurKrd")
        return
    await set_channels_from_text(update.effective_message, raw)


async def set_channels_from_text(message, raw: str) -> None:
    channels = [x.strip() for x in raw.replace(";", ",").replace(" ", ",").split(",") if x.strip()]
    data = state.load(); data["channels"] = channels; state.save(data)
    await message.reply_text("Каналы заменены:\n" + ("\n".join(f"• {c}" for c in channels) or "не заданы"), reply_markup=main_menu())


async def autopost_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load(); data["autopost_enabled"] = True; state.save(data)
    scheduler.reschedule(data.get("schedule_times", ["09:00", "14:00", "19:00"]), lambda: scheduled_autopost(context.application))
    await update.effective_message.reply_text("Автопостинг включён.", reply_markup=main_menu())


async def autopost_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load(); data["autopost_enabled"] = False; state.save(data)
    await update.effective_message.reply_text("Автопостинг выключен.", reply_markup=main_menu())


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    if context.args and context.args[0].isdigit():
        idx = int(context.args[0])
    else:
        idx = state.next_test_index()
    await update.effective_message.reply_text("Ищу новую тему и готовлю один лучший пост через OpenAI…")
    pipeline = EditorialPipeline(settings, bot=context.bot)
    prepared, report = await pipeline.prepare_post(test_index=idx, remember_preview=True)
    if not prepared:
        await send_long(update.effective_message, report.admin_text())
        return
    writer = TelegramPostWriter()
    header = (
        f"🧪 Тест темы\n"
        f"Источник: {prepared.signal.source_name}\n"
        f"Жанр: {prepared.brief.genre} · слот: {prepared.brief.slot} · score: {prepared.signal.score}\n"
        f"Угол: {prepared.brief.editorial_angle}\n"
    )
    await update.effective_message.reply_text(header)
    best = prepared.best_variant()
    preview = writer.preview(best, prepared.brief)
    await update.effective_message.reply_text(
        f"Пост · {best.style} · качество {best.score}/100\n\n{preview[:3500]}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    buttons = [
        [InlineKeyboardButton("🚀 Опубликовать", callback_data=f"publish:{prepared.session_id}:{best.variant_id}")],
        [InlineKeyboardButton("🔁 Новая тема", callback_data=f"rewrite:{idx + 1}"), InlineKeyboardButton("⛔ Отклонить", callback_data=f"reject:{prepared.session_id}")],
    ]
    await update.effective_message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(buttons))
    await send_long(update.effective_message, report.admin_text())


async def run_once_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    await update.effective_message.reply_text("Запуск начат. Собираю источники, выбираю тему, генерирую через OpenAI и публикую онлайн…")
    pipeline = EditorialPipeline(settings, bot=context.bot)
    prepared, result, report = await pipeline.run_once()
    await send_long(update.effective_message, report.admin_text())


async def why_skipped_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load(); last = data.get("last_run") or {}
    await send_long(update.effective_message, last.get("message") or "Последней причины пропуска нет.")


async def last_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    data = state.load(); last = data.get("last_run") or {}
    if last:
        from .diagnostics import RunReport
        r = RunReport()
        r.run_id = last.get("run_id", r.run_id)
        r.started_at = last.get("started_at", "")
        r.finished_at = last.get("finished_at", "")
        r.steps = last.get("steps", [])
        r.counters = last.get("counters", {})
        r.source_errors = last.get("source_errors", {})
        r.result = last.get("result", "")
        r.message = last.get("message", "")
        await send_long(update.effective_message, r.admin_text())
        return
    await update.effective_message.reply_text("Отчётов пока нет.")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not is_admin(update):
        return
    data = q.data or ""
    if data.startswith("publish:"):
        _, session_id, variant_s = data.split(":", 2)
        session = state.get_session(session_id)
        if not session:
            await q.edit_message_text("Сессия не найдена. Запустите тест заново.")
            return
        prepared = prepared_from_dict(session)
        pipeline = EditorialPipeline(settings, bot=context.bot)
        result, report = await pipeline.publish_prepared(prepared, variant_id=int(variant_s))
        await q.edit_message_text("Публикация выполнена. Ниже полный отчёт.")
        await send_long(q.message, report.admin_text())
    elif data.startswith("rewrite:"):
        await q.edit_message_text("Запускаю новую тему…")
        await q.message.reply_text("Нажмите кнопку «🧪 Тест поста» или отправьте /test для новой темы.", reply_markup=main_menu())
    elif data.startswith("reject:"):
        await q.edit_message_text("Тема отклонена. Нажмите «🧪 Тест поста» для новой темы.")


def prepared_from_dict(data: dict[str, Any]) -> PreparedPost:
    signal = Signal(**data["signal"])
    brief = Brief(**data["brief"])
    variants = [PostVariant.from_dict(v) for v in data.get("variants", [])]
    media = MediaAsset(**data.get("media", {}))
    return PreparedPost(
        session_id=data["session_id"],
        signal=signal,
        brief=brief,
        variants=variants,
        best_variant_id=data.get("best_variant_id", 1),
        media=media,
        diagnostics=data.get("diagnostics", {}),
    )


async def menu_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await admin_only(update):
        return
    text = (update.effective_message.text or "").strip()
    awaiting = context.user_data.pop("awaiting", None)
    if awaiting == "set_schedule":
        await set_schedule_from_text(update.effective_message, text, context)
        return
    if awaiting == "add_channel":
        await add_channels_from_text(update.effective_message, text)
        return
    if awaiting == "set_channels":
        await set_channels_from_text(update.effective_message, text)
        return

    if text == BTN_TEST:
        context.args = []
        await test_cmd(update, context)
    elif text == BTN_PUBLISH:
        await run_once_cmd(update, context)
    elif text == BTN_STATUS:
        await status_cmd(update, context)
    elif text == BTN_LAST:
        await last_cmd(update, context)
    elif text == BTN_SCHEDULE:
        await schedule_cmd(update, context)
    elif text == BTN_SET_SCHEDULE:
        context.user_data["awaiting"] = "set_schedule"
        await update.effective_message.reply_text("Введите новое расписание: 09:00,14:00,19:00")
    elif text == BTN_CHANNELS:
        await channels_cmd(update, context)
    elif text == BTN_ADD_CHANNEL:
        context.user_data["awaiting"] = "add_channel"
        await update.effective_message.reply_text("Введите канал для добавления: @channel")
    elif text == BTN_SET_CHANNELS:
        context.user_data["awaiting"] = "set_channels"
        await update.effective_message.reply_text("Введите новый список каналов через запятую: @test,@NadoTurKrd")
    elif text == BTN_AUTOP_ON:
        await autopost_on_cmd(update, context)
    elif text == BTN_AUTOP_OFF:
        await autopost_off_cmd(update, context)
    elif text == BTN_SOURCES:
        await sources_cmd(update, context)
    elif text == BTN_MENU:
        await start_cmd(update, context)
    else:
        await update.effective_message.reply_text("Не понял команду. Используйте кнопки меню.", reply_markup=main_menu())


async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Команда не распознана. Используйте /menu или кнопки управления.", reply_markup=main_menu())


async def scheduled_autopost(app: Application) -> None:
    data = state.load()
    if not data.get("autopost_enabled"):
        return
    pipeline = EditorialPipeline(settings, bot=app.bot)
    prepared, result, report = await pipeline.run_once()
    if settings.telegram_admin_id:
        try:
            await app.bot.send_message(chat_id=int(settings.telegram_admin_id), text=report.admin_text()[:3900])
        except Exception:
            log.exception("Не удалось отправить отчёт админу")


async def post_init(app: Application) -> None:
    scheduler.start()
    data = state.load()
    if data.get("autopost_enabled"):
        scheduler.reschedule(data.get("schedule_times", ["09:00", "14:00", "19:00"]), lambda: scheduled_autopost(app))


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
        ("topics", topics_cmd), ("why_skipped", why_skipped_cmd), ("last", last_cmd),
    ]
    for name, func in commands:
        app.add_handler(CommandHandler(name, func))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))
    return app


def main() -> None:
    app = build_app()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
