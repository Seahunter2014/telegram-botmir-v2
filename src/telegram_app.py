import asyncio
import json
import logging
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from .version import VERSION, PROJECT_NAME
from .config_loader import env, ensure_dirs
from .state_store import StateStore
from .source_manager import SourceManager
from .topic_guard import TopicGuard
from .topic_classifier import TopicClassifier
from .scoring_engine import ScoringEngine
from .rotation_engine import RotationEngine
from .dedup_engine import DedupEngine
from .editorial_brief_engine import EditorialBriefEngine
from .ai_writer import AIWriter
from .editorial_polisher import EditorialPolisher
from .quality_selector import QualitySelector
from .cta_engine import CTAEngine
from .media_engine import MediaEngine
from .telegram_post_writer import TelegramPostWriter
from .publisher import Publisher
from .analytics_store import AnalyticsStore
from .scheduler import NewsroomScheduler
from .menu import main_menu, draft_keyboard
from .text_utils import hash_text, html_escape

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("ai_newsroom_bot")

state = StateStore()
sources = SourceManager()
guard = TopicGuard()
classifier = TopicClassifier()
scoring = ScoringEngine()
rotation = RotationEngine(state)
dedup = DedupEngine(state)
brief_engine = EditorialBriefEngine()
polisher = EditorialPolisher()
quality = QualitySelector()
cta = CTAEngine()
media_engine = MediaEngine()
post_writer = TelegramPostWriter()
analytics = AnalyticsStore(state)
scheduler = NewsroomScheduler()


def admin_only(update: Update) -> bool:
    admin_id = env("TELEGRAM_ADMIN_ID")
    if not admin_id:
        return True
    user = update.effective_user
    return bool(user and str(user.id) == str(admin_id))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"<b>{PROJECT_NAME}</b>\nВерсия: <code>{VERSION}</code>\n\nВыберите действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )

async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(f"<code>{VERSION}</code>", parse_mode=ParseMode.HTML)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = state.load()
    text = (
        f"<b>Статус AI-редакции</b>\n"
        f"Автопостинг: {'включён' if data.get('autopost_enabled') else 'выключен'}\n"
        f"Расписание: {', '.join(data.get('schedule_times', []))}\n"
        f"Каналы: {', '.join(data.get('channels', [])) or 'не заданы'}\n"
        f"Тестовый канал: {data.get('test_channel') or 'не задан'}\n"
        f"Последний пропуск: {html_escape(data.get('last_skip_reason','')) or 'нет'}"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())

async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    times = state.get("schedule_times", [])
    await update.effective_message.reply_text(
        "<b>Расписание автопостинга</b>\n"
        f"Сейчас: <code>{', '.join(times)}</code>\n\n"
        "Чтобы заменить расписание, отправьте:\n"
        "<code>/schedule_set 09:00,14:00,19:00</code>",
        parse_mode=ParseMode.HTML
    )

async def schedule_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update): return
    raw = " ".join(context.args).replace(";", ",")
    times = [x.strip() for x in raw.split(",") if x.strip()]
    good = []
    for t in times:
        if re.match(r"^\d{1,2}:\d{2}$", t):
            h, m = [int(x) for x in t.split(":")]
            if 0 <= h <= 23 and 0 <= m <= 59:
                good.append(f"{h:02d}:{m:02d}")
    if not good:
        await update.effective_message.reply_text("Не понял расписание. Пример: /schedule_set 09:00,14:00,19:00")
        return
    state.set("schedule_times", good)
    scheduler.reschedule(good, lambda: context.application.create_task(run_autopost(context.application.bot)))
    await update.effective_message.reply_text(f"Готово. Новое расписание: {', '.join(good)}")

async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = state.load()
    await update.effective_message.reply_text(
        "<b>Каналы публикации</b>\n"
        f"Сейчас: <code>{', '.join(data.get('channels', [])) or 'не заданы'}</code>\n\n"
        "Команды:\n"
        "<code>/add_channel @channel</code> — добавить канал\n"
        "<code>/remove_channel @channel</code> — удалить канал\n"
        "<code>/set_channels @ch1,@ch2</code> — заменить список\n\n"
        "Бот должен быть администратором в каждом канале.",
        parse_mode=ParseMode.HTML
    )

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update): return
    ch = " ".join(context.args).strip()
    if not ch:
        await update.effective_message.reply_text("Укажите канал: /add_channel @channel")
        return
    data = state.load()
    arr = data.setdefault("channels", [])
    if ch not in arr:
        arr.append(ch)
    state.save(data)
    await update.effective_message.reply_text(f"Канал добавлен: {ch}")

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update): return
    ch = " ".join(context.args).strip()
    data = state.load()
    arr = [x for x in data.get("channels", []) if x != ch]
    data["channels"] = arr
    state.save(data)
    await update.effective_message.reply_text(f"Готово. Каналы: {', '.join(arr) or 'нет'}")

async def set_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update): return
    raw = " ".join(context.args).strip()
    arr = [x.strip() for x in raw.split(",") if x.strip()]
    state.set("channels", arr)
    await update.effective_message.reply_text(f"Каналы заменены: {', '.join(arr) or 'нет'}")

async def autopost_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.set("autopost_enabled", True)
    scheduler.reschedule(state.get("schedule_times", []), lambda: context.application.create_task(run_autopost(context.application.bot)))
    await update.effective_message.reply_text("Автопостинг включён.")

async def autopost_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.set("autopost_enabled", False)
    await update.effective_message.reply_text("Автопостинг выключен.")

async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [f"• {s['name']} — {s['url']}" for s in sources.list_sources()]
    await update.effective_message.reply_text("<b>Источники</b>\n" + "\n".join(lines[:30]), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def list_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .config_loader import read_json
    services = read_json("services.json", [])
    lines = [f"• {s['name']} ({s['key']}) — {s['url']}" for s in services]
    await update.effective_message.reply_text("<b>Сервисы</b>\n" + "\n".join(lines[:40]), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update): return
    arg = " ".join(context.args).strip()
    await build_and_send_preview(update, context, arg)

async def text_test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.effective_message.text or "").strip().lower()
    m = re.match(r"^(?:тест|test)\s*(\d+|[a-z_]+)?$", txt)
    if m:
        await build_and_send_preview(update, context, m.group(1) or "")

async def build_and_send_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, arg: str = ""):
    try:
        offset = 0
        genre_filter = ""
        if arg and arg.isdigit():
            offset = max(0, int(arg) - 1)
        elif arg:
            genre_filter = arg
        else:
            offset = state.get("test_cursor", 0)
            state.set("test_cursor", offset + 1)
        signal = sources.fetch_for_test(offset=offset, genre=genre_filter)
        if not signal:
            await update.effective_message.reply_text("Не нашёл подходящую тему для теста.")
            return
        session_id, brief, generated = await create_draft_session(signal, context)
        if generated.decision != "publishable" or not generated.variants:
            await update.effective_message.reply_text(f"Тема отклонена редактором: {generated.reject_reason}")
            return
        header = (
            f"<b>Тест темы</b>\n"
            f"Источник: {html_escape(signal.source_name)}\n"
            f"Жанр: <code>{brief.genre}</code> · слот: <code>{brief.slot}</code> · score: <code>{brief.score}</code>\n"
            f"Угол: {html_escape(brief.editorial_angle)}\n"
            f"Ссылка: {html_escape(signal.url or signal.source_url)}"
        )
        await update.effective_message.reply_text(header, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        for variant in generated.variants:
            await update.effective_message.reply_text(post_writer.format_preview(variant), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        await update.effective_message.reply_text("Выберите действие:", reply_markup=draft_keyboard(session_id))
    except Exception as exc:
        log.exception("test failed")
        await update.effective_message.reply_text(f"Ошибка теста: {html_escape(str(exc))}", parse_mode=ParseMode.HTML)

async def create_draft_session(signal, context, mode: str = "normal"):
    ok, reason = guard.check(signal)
    if not ok:
        state.set("last_skip_reason", reason)
        raise RuntimeError(f"Тема отклонена фильтром: {reason}")
    dup, dup_reason = dedup.is_duplicate_signal(signal)
    if dup:
        state.set("last_skip_reason", dup_reason)
        raise RuntimeError(f"Дубль: {dup_reason}")
    slot = rotation.current_slot()
    genre = classifier.classify(signal)
    score, warnings = scoring.score(signal, genre, slot)
    brief = brief_engine.build(signal, genre, slot, score, warnings)
    generated = AIWriter().generate(brief, mode=mode)
    for v in generated.variants:
        polisher.polish(v)
        cta.apply(brief, v)
    best, notes = quality.select_best(generated)
    if best:
        generated.best_variant_id = best.variant_id
    session_id = state.new_session_id()
    state.store_draft_session(session_id, {
        "brief": brief_to_dict(brief),
        "post": post_to_dict(generated),
    })
    return session_id, brief, generated

async def run_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update): return
    result = await run_autopost(context.application.bot, force=True)
    await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)

async def run_autopost(bot, force: bool = False) -> str:
    if not force and not state.get("autopost_enabled", False):
        return "Автопостинг выключен."

    allow_fallback = env("ALLOW_FALLBACK_AUTOPUBLISH", "false").lower() == "true"
    signals = sources.fetch_signals(limit_per_source=4, include_fallback=allow_fallback)
    slot = rotation.current_slot()
    last_reason = "Нет сигналов."
    ranked = []

    # Stage 1: filter and rank all candidates first. Do NOT publish the first acceptable item.
    for signal in signals[:120]:
        try:
            ok, reason = guard.check(signal)
            if not ok:
                last_reason = reason
                continue

            dup, reason = dedup.is_duplicate_signal(signal)
            if dup:
                last_reason = reason
                continue

            genre = classifier.classify(signal)
            score, warnings = scoring.score(signal, genre, slot)
            if score < 60:
                last_reason = f"Низкий score {score}"
                continue

            brief = brief_engine.build(signal, genre, slot, score, warnings)
            rot_ok, rot_reason = rotation.allowed(brief.genre, brief.route_to, brief.country, signal.source_key)
            if not rot_ok:
                last_reason = rot_reason
                continue

            # Prefer slot fit, then score, but keep source-diversified order as tie-breaker.
            slot_bonus = 20 if genre in scoring.slot_genres(slot) else 0
            ranked.append((score + slot_bonus, brief, signal))
        except Exception as exc:
            last_reason = str(exc)
            log.warning("autopost candidate prefilter failed: %s", exc)

    ranked.sort(key=lambda item: item[0], reverse=True)

    # Stage 2: generate only for the best ranked candidates, until one passes quality gate.
    for _, brief, signal in ranked[:12]:
        try:
            generated = AIWriter().generate(brief)
            if generated.decision != "publishable" or not generated.variants:
                last_reason = generated.reject_reason or "Редактор отклонил тему"
                continue

            for v in generated.variants:
                polisher.polish(v)
                cta.apply(brief, v)

            best, notes = quality.select_best(generated)
            if not best or best.score < 70:
                last_reason = "Лучший вариант не прошёл quality gate"
                continue

            media = media_engine.choose_media(brief, best, generated.media_query)
            pub = Publisher(bot)
            channels = state.get("channels", [])
            if not channels:
                return "Каналы не заданы. Добавьте канал через /add_channel @channel"

            for ch in channels:
                await pub.publish_to_channel(ch, best, media)

            record_publication(brief, best)
            analytics.record_publication({"genre": brief.genre, "source": signal.source_key, "title": best.title, "channels": channels})
            return f"Опубликовано: <b>{html_escape(best.title)}</b>"
        except Exception as exc:
            last_reason = str(exc)
            log.warning("autopost candidate failed: %s", exc)

    state.set("last_skip_reason", last_reason)
    return f"Публикация не выполнена. Причина: {html_escape(last_reason)}"
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    if data == "menu:test":
        await build_and_send_preview(update, context, "")
    elif data == "menu:status":
        await status(update, context)
    elif data == "menu:schedule":
        await schedule_cmd(update, context)
    elif data == "menu:channels":
        await channels_cmd(update, context)
    elif data == "menu:autopost_on":
        state.set("autopost_enabled", True); await q.edit_message_text("Автопостинг включён.")
    elif data == "menu:autopost_off":
        state.set("autopost_enabled", False); await q.edit_message_text("Автопостинг выключен.")
    elif data.startswith("pub:"):
        _, session_id, variant_id = data.split(":")
        await publish_variant(q, context, session_id, int(variant_id))
    elif data.startswith("reject:"):
        await q.edit_message_text("Тема отклонена.")
    elif data.startswith("regen:"):
        await q.edit_message_text("Перегенерация через меню будет добавлена как отдельный сценарий. Сейчас используйте /test для новой темы или /test 1 для конкретной.")

async def publish_variant(q, context, session_id: str, variant_id: int):
    session = state.get_draft_session(session_id)
    if not session:
        await q.edit_message_text("Сессия не найдена. Запустите /test заново.")
        return
    brief = dict_to_brief(session["brief"])
    generated = dict_to_post(session["post"])
    variant = next((v for v in generated.variants if v.variant_id == variant_id), None)
    if not variant:
        await q.edit_message_text("Вариант не найден.")
        return
    media = media_engine.choose_media(brief, variant, generated.media_query)
    pub = Publisher(context.application.bot)
    channels = state.get("channels", [])
    if not channels:
        await q.edit_message_text("Каналы не заданы. Добавьте канал через /add_channel @channel")
        return
    for ch in channels:
        await pub.publish_to_channel(ch, variant, media)
    record_publication(brief, variant)
    await q.edit_message_text(f"Опубликовано в {len(channels)} канал(а/ов): {variant.title}")

def record_publication(brief, variant):
    signal = brief.signal
    state.append_unique("published_urls", signal.url)
    state.append_unique("published_titles", variant.title)
    state.append_unique("published_text_hashes", hash_text(variant.title + variant.body))
    state.append_unique("published_genres", brief.genre)
    state.append_unique("published_sources", signal.source_key)
    if brief.route_to:
        state.append_unique("published_cities", brief.route_to)

def brief_to_dict(brief):
    return {
        "signal": brief.signal.__dict__, "genre": brief.genre, "slot": brief.slot, "score": brief.score,
        "city": brief.city, "country": brief.country, "route_from": brief.route_from, "route_to": brief.route_to,
        "price": brief.price, "date_text": brief.date_text, "editorial_angle": brief.editorial_angle,
        "target_emotion": brief.target_emotion, "allowed_services": brief.allowed_services, "warnings": brief.warnings
    }

def post_to_dict(post):
    return {
        "decision": post.decision, "reject_reason": post.reject_reason, "genre": post.genre, "slot": post.slot,
        "editorial_angle": post.editorial_angle, "target_emotion": post.target_emotion,
        "media_query": post.media_query, "media_requirements": post.media_requirements,
        "best_variant_id": post.best_variant_id,
        "variants": [{**v.__dict__, "buttons": [b.__dict__ for b in v.buttons]} for v in post.variants]
    }

def dict_to_brief(d):
    from .models import Signal, EditorialBrief
    sig = Signal(**d["signal"])
    d2 = {k:v for k,v in d.items() if k != "signal"}
    return EditorialBrief(signal=sig, **d2)

def dict_to_post(d):
    from .models import GeneratedPost, PostVariant, Button
    variants=[]
    for item in d.get("variants", []):
        buttons=[Button(**b) for b in item.pop("buttons", [])]
        variants.append(PostVariant(**item, buttons=buttons))
    return GeneratedPost(**{k:v for k,v in d.items() if k != "variants"}, variants=variants)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Telegram error", exc_info=context.error)


async def post_init(app: Application):
    # APScheduler must be started only after PTB has created the running event loop.
    scheduler.start()
    scheduler.reschedule(
        state.get("schedule_times", []),
        lambda: app.create_task(run_autopost(app.bot))
    )
    log.info("Autopost schedule loaded: %s", ", ".join(state.get("schedule_times", [])))


async def post_shutdown(app: Application):
    scheduler.shutdown()


def main():
    ensure_dirs()
    token = env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")
    app = Application.builder().token(token).post_init(post_init).post_shutdown(post_shutdown).build()
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CommandHandler("version", version))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CommandHandler("preview", test_cmd))
    app.add_handler(CommandHandler("run_once", run_once))
    app.add_handler(CommandHandler("schedule", schedule_cmd))
    app.add_handler(CommandHandler("schedule_set", schedule_set))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("set_channels", set_channels))
    app.add_handler(CommandHandler("autopost_on", autopost_on))
    app.add_handler(CommandHandler("autopost_off", autopost_off))
    app.add_handler(CommandHandler("sources", list_sources))
    app.add_handler(CommandHandler("services", list_services))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_test_handler))
    app.add_error_handler(error_handler)
    log.info("Starting %s", VERSION)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
