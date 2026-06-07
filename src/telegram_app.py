from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from src import BOT_VERSION
from src.ai_writer import rewrite_variant
from src.config_loader import load_config
from src.newsroom import create_package
from src.publisher import publish_to_channel, render_post, render_post_html
from src.quality_selector import score_variant, select_best_variant
from src.scheduler import build_scheduler, set_autopost, set_schedule
from src.state_store import append_rejected, load_publication_log, load_state, record_skip, remember_publication

if load_dotenv:
    load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("mir_na_ladoni.newsroom")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN = os.getenv("TELEGRAM_ADMIN_ID", "").strip()
CHANNEL = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
TEST_CHANNEL = os.getenv("TEST_CHANNEL_ID", "").strip()


def admin_id() -> int | None:
    try:
        return int(ADMIN) if ADMIN else None
    except ValueError:
        return None


async def reply(
    update: Update,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    kwargs = {"reply_markup": markup, "disable_web_page_preview": True}
    if parse_mode:
        kwargs["parse_mode"] = parse_mode
    if update.message:
        await update.message.reply_text(text[:3900], **kwargs)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text[:3900], **kwargs)


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        aid = admin_id()
        if aid is None:
            await reply(update, "Не задан TELEGRAM_ADMIN_ID в Railway Variables.")
            return
        if not update.effective_user or update.effective_user.id != aid:
            await reply(update, "Доступ только для администратора.")
            return
        return await func(update, context)

    return wrapper


def bundle(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["bundle"]


def channel_id(context: ContextTypes.DEFAULT_TYPE) -> str:
    return os.getenv("TELEGRAM_CHANNEL_ID", CHANNEL).strip()


def test_channel_id(context: ContextTypes.DEFAULT_TYPE) -> str:
    return os.getenv("TEST_CHANNEL_ID", TEST_CHANNEL).strip() or channel_id(context)


def drafts(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    return context.application.bot_data.setdefault("drafts", {})


def variant_keyboard(package: dict) -> InlineKeyboardMarkup:
    package_id = package["id"]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Опубликовать 1 в тест", callback_data=f"publish:{package_id}:0"),
                InlineKeyboardButton("Опубликовать 2 в тест", callback_data=f"publish:{package_id}:1"),
                InlineKeyboardButton("Опубликовать 3 в тест", callback_data=f"publish:{package_id}:2"),
            ],
            [
                InlineKeyboardButton("Переписать", callback_data=f"rewrite:{package_id}:best"),
                InlineKeyboardButton("Мягче", callback_data=f"softer:{package_id}:best"),
                InlineKeyboardButton("Сильнее", callback_data=f"sales:{package_id}:best"),
            ],
            [InlineKeyboardButton("Отклонить тему", callback_data=f"reject:{package_id}:0")],
        ]
    )


def summary(package: dict) -> str:
    plan = package["plan"]
    signal = package["signal"]
    cta = package.get("cta", {})
    return (
        f"Пакет: {package['id']}\n"
        f"Источник: {signal.get('source_name')}\n"
        f"Ссылка: {signal.get('url')}\n"
        f"Жанр: {plan.get('topic')} / {plan.get('genre')}\n"
        f"Слот: {plan.get('slot_ru')}\n"
        f"Score темы: {plan.get('score', {}).get('score')}\n"
        f"Почему выбрано: {plan.get('hook_angle')}\n"
        f"Прямой оффер: {'да' if plan.get('has_direct_offer') else 'нет'}\n"
        f"Кнопок: {len(cta.get('buttons', []))}"
    )


async def send_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, package: dict) -> None:
    drafts(context)[package["id"]] = package
    await reply(update, summary(package))
    for index, variant in enumerate(package["variants"], 1):
        quality = variant.get("quality", {})
        text = f"ВАРИАНТ {index}\nОценка: {quality.get('score')}\nСтиль: {variant.get('style')}\n\n"
        text += render_post_html(variant, package["plan"], package["signal"])
        await reply(update, text, parse_mode=ParseMode.HTML)
    await reply(update, "Выберите действие:", variant_keyboard(package))


@admin_only
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(
        update,
        "AI-редакция «Мир на ладони» готова.\n\n"
        "/test — 3 варианта\n"
        "/preview — предпросмотр\n"
        "/publish — опубликовать лучший текущий вариант в тестовый канал\n"
        "/autopost_on /autopost_off — автопостинг\n"
        "/schedule 09:00,14:00,19:00 — расписание\n"
        "/status — статус\n"
        "/last — последняя публикация\n"
        "/why_skipped — последний пропуск\n"
        "/sources /topics /services — реестры\n"
        "/version — версия"
    )


@admin_only
async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    current_bundle = bundle(context)
    await reply(
        update,
        f"mirnala_bot_v3 — {BOT_VERSION}\n"
        f"Проект: {current_bundle.policy.get('project_name')}\n"
        f"Тем: {len(current_bundle.topics['topics'])}\n"
        f"Источников: {len(current_bundle.sources['sources'])}\n"
        f"Сервисов: {len(current_bundle.services['services'])}\n"
        f"Канал: {channel_id(context) or 'не задан'}\n"
        f"Тестовый канал: {test_channel_id(context) or 'не задан'}\n"
        f"Автопостинг: {'вкл' if state.get('autopost_enabled') else 'выкл'}\n"
        f"Расписание: {', '.join(state.get('post_times', current_bundle.policy.get('default_post_times', [])))}"
    )


@admin_only
async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    topic = context.args[0] if context.args else None
    try:
        package = create_package(bundle(context), forced_topic=topic, allow_media=True, require_minimum_quality=False)
        await send_preview(update, context, package)
    except Exception as exc:
        record_skip("test_failed", str(exc))
        await reply(update, f"Тест не собрался: {exc}")


@admin_only
async def preview_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await test_cmd(update, context)


@admin_only
async def publish_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not drafts(context):
        await reply(update, "Нет готового пакета. Сначала выполните /test.")
        return
    package = list(drafts(context).values())[-1]
    variant = package.get("best_variant") or select_best_variant(package["variants"], package["plan"], bundle(context))
    target = test_channel_id(context)
    if not target:
        await reply(update, "Не задан TEST_CHANNEL_ID или TELEGRAM_CHANNEL_ID.")
        return
    used = await publish_to_channel(context.bot, target, variant, package["media"], package["plan"], package["signal"])
    remember_publication(package, variant, "manual_publish", used)
    await reply(update, f"Опубликовано в {target}.")


@admin_only
async def autopost_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_autopost(True)
    build_scheduler(context.application)
    await reply(update, "Автопостинг включён.")


@admin_only
async def autopost_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_autopost(False)
    await reply(update, "Автопостинг выключен.")


@admin_only
async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        times = " ".join(context.args).replace(" ", "").split(",")
        if len(times) != 3 or any(":" not in time_value for time_value in times):
            await reply(update, "Формат: /schedule 09:00,14:00,19:00")
            return
        set_schedule(times)
        build_scheduler(context.application)
        await reply(update, "Расписание обновлено: " + ", ".join(times))
        return
    await reply(update, "Расписание: " + ", ".join(load_state().get("post_times", [])))


@admin_only
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    await reply(
        update,
        f"Автопостинг: {'вкл' if state.get('autopost_enabled') else 'выкл'}\n"
        f"Последний пропуск: {state.get('last_skip_report') or '—'}\n"
        f"Последний выбор: {state.get('last_selection_report') or '—'}"
    )


@admin_only
async def last_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log = load_publication_log()
    await reply(update, str(log[-1])[:3900] if log else "Публикаций пока нет.")


@admin_only
async def why_skipped_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, str(load_state().get("last_skip_report") or "Пропусков пока нет.")[:3900])


@admin_only
async def sources_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, "\n".join(["Источники:"] + [f"- {source['name']} — {source['endpoint']}" for source in bundle(context).sources["sources"]])[:3900])


@admin_only
async def topics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, "\n".join(["Темы:"] + [f"- {topic['key']} — {topic['name']}" for topic in bundle(context).topics["topics"]])[:3900])


@admin_only
async def services_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, "\n".join(["Сервисы:"] + [f"- {service['name']} — {service['ref_url']}" for service in bundle(context).services["services"]])[:3900])


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if admin_id() is None or not query.from_user or query.from_user.id != admin_id():
        await query.message.reply_text("Доступ только для администратора.")
        return
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        return
    action, package_id, value = parts[0], parts[1], parts[2]
    package = drafts(context).get(package_id)
    if not package:
        await query.message.reply_text("Пакет не найден. Выполните /test заново.")
        return
    if action == "publish":
        index = int(value)
        variant = package["variants"][index]
        target = test_channel_id(context)
        used = await publish_to_channel(context.bot, target, variant, package["media"], package["plan"], package["signal"])
        remember_publication(package, variant, "manual_approved", used)
        await query.message.reply_text(f"Опубликован вариант {index + 1} в {target}.")
        return
    if action in {"rewrite", "softer", "sales"}:
        try:
            base = package.get("best_variant") or package["variants"][0]
            new_variant = rewrite_variant(base, package["plan"], package["signal"], bundle(context), action)
            new_variant["quality"] = score_variant(new_variant, package["plan"], bundle(context))
            package["variants"] = [new_variant] + package["variants"][:2]
            package["best_variant"] = select_best_variant(package["variants"], package["plan"], bundle(context))
            drafts(context)[package_id] = package
            await query.message.reply_text(render_post_html(new_variant, package["plan"], package["signal"])[:3600], parse_mode=ParseMode.HTML, reply_markup=variant_keyboard(package))
        except Exception as exc:
            await query.message.reply_text(f"Не удалось переписать: {exc}")
        return
    if action == "reject":
        append_rejected({"package": package_id, "signal": package.get("signal"), "plan": package.get("plan")})
        drafts(context).pop(package_id, None)
        await query.message.reply_text("Тема отклонена. Можно выполнить /test заново.")


async def post_init(application: Application) -> None:
    current_bundle = load_config()
    application.bot_data["bundle"] = current_bundle
    application.bot_data["channel_id"] = CHANNEL
    application.bot_data["test_channel_id"] = TEST_CHANNEL
    build_scheduler(application)


def build_application() -> Application:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    for name, func in [
        ("start", start_cmd),
        ("version", version_cmd),
        ("test", test_cmd),
        ("preview", preview_cmd),
        ("publish", publish_cmd),
        ("autopost_on", autopost_on_cmd),
        ("autopost_off", autopost_off_cmd),
        ("schedule", schedule_cmd),
        ("status", status_cmd),
        ("last", last_cmd),
        ("why_skipped", why_skipped_cmd),
        ("sources", sources_cmd),
        ("topics", topics_cmd),
        ("services", services_cmd),
    ]:
        app.add_handler(CommandHandler(name, func))
    app.add_handler(CallbackQueryHandler(callback_handler))
    return app


def main() -> None:
    logger.info("BOOT VERSION: %s", BOT_VERSION)
    build_application().run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
