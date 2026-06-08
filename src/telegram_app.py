import html
import logging
import re
from typing import Any

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .ai_writer import AIWriter
from .analytics_store import AnalyticsStore
from .config_loader import ensure_dirs, env, read_json
from .cta_engine import CTAEngine
from .dedup_engine import DedupEngine
from .editorial_brief_engine import EditorialBriefEngine
from .editorial_polisher import EditorialPolisher
from .engagement_engine import EngagementEngine
from .fact_checker import FactChecker
from .media_engine import MediaEngine
from .menu import channels_menu, draft_keyboard, main_menu, schedule_menu
from .models import Button, EditorialBrief, GeneratedPost, PostVariant, Signal
from .publisher import Publisher
from .quality_selector import QualitySelector
from .rotation_engine import RotationEngine
from .scheduler import NewsroomScheduler
from .scoring_engine import ScoringEngine
from .source_manager import SourceManager
from .state_store import StateStore
from .telegram_post_writer import TelegramPostWriter
from .text_utils import hash_text, html_escape, normalize_title
from .topic_classifier import TopicClassifier
from .topic_guard import TopicGuard
from .version import PROJECT_NAME, VERSION

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("ai_newsroom_bot")

POLICY = read_json("editorial_policy.json", {})
TOPICS_ORDER = read_json("topics.json", [])
QUALITY_MIN_PUBLICATION_SCORE = int(POLICY.get("quality_min_publication_score", 85))
AUTOPOST_MIN_LOCAL_SCORE = int(POLICY.get("autopost_min_local_score", 70))

PENDING_ACTION_KEY = "pending_action"

state = StateStore()
sources = SourceManager(state)
guard = TopicGuard()
classifier = TopicClassifier()
scoring = ScoringEngine()
rotation = RotationEngine(state)
dedup = DedupEngine(state)
brief_engine = EditorialBriefEngine()
writer = AIWriter()
engagement = EngagementEngine()
polisher = EditorialPolisher()
quality = QualitySelector()
fact_checker = FactChecker()
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


def parse_schedule_string(raw: str) -> list[str]:
    items = [item.strip() for item in raw.replace(";", ",").split(",") if item.strip()]
    result: list[str] = []
    for item in items:
        if not re.match(r"^\d{1,2}:\d{2}$", item):
            continue
        hour, minute = [int(part) for part in item.split(":")]
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            result.append(f"{hour:02d}:{minute:02d}")
    deduped: list[str] = []
    for item in result:
        if item not in deduped:
            deduped.append(item)
    return deduped


def parse_channel_list(raw: str) -> list[str]:
    parts = re.split(r"[\s,;]+", raw.strip())
    result: list[str] = []
    for item in parts:
        if not item:
            continue
        cleaned = item if item.startswith("@") else item
        if cleaned not in result:
            result.append(cleaned)
    return result


def safe_source_link(signal: Signal) -> str:
    link = signal.url or signal.source_url or ""
    if not link:
        return "нет"
    return f'<a href="{html.escape(link, quote=True)}">открыть источник</a>'


def is_rejected_signal(signal: Signal) -> tuple[bool, str]:
    rejected = state.get("rejected_topics", []) or []
    title_norm = normalize_title(signal.title)
    for item in rejected[-200:]:
        if isinstance(item, dict):
            if signal.url and item.get("url") == signal.url:
                return True, "Эта тема уже отклонялась вручную."
            old_title = item.get("title", "")
            if old_title and title_norm and normalize_title(old_title) == title_norm:
                return True, "Похожая тема уже отклонялась вручную."
        elif isinstance(item, str) and title_norm and normalize_title(item) == title_norm:
            return True, "Похожая тема уже отклонялась вручную."
    return False, ""


def remember_rejected_signal(signal: Signal, reason: str = "") -> None:
    payload = {
        "title": signal.title,
        "url": signal.url,
        "source_key": signal.source_key,
        "source_name": signal.source_name,
        "reason": reason or "Отклонено администратором",
    }
    data = state.load()
    rejected = data.setdefault("rejected_topics", [])
    rejected.append(payload)
    data["rejected_topics"] = rejected[-200:]
    data["last_skip_reason"] = payload["reason"]
    state.save(data)
    state.append_json_list("rejected_topics.json", payload, limit=500)


def manual_target_channels() -> list[str]:
    test_channel = state.get("test_channel", "") or env("TEST_CHANNEL_ID")
    if test_channel:
        return [test_channel]
    channels = state.get("channels", []) or []
    return channels[:1]


def autopost_target_channels() -> list[str]:
    channels = state.get("channels", []) or []
    env_channel = env("TELEGRAM_CHANNEL_ID")
    if env_channel and env_channel not in channels:
        channels.append(env_channel)
    return channels


def apply_schedule(raw: str) -> list[str]:
    times = parse_schedule_string(raw)
    if not times:
        raise ValueError("Не удалось распознать расписание. Пример: 09:00,14:00,19:00")
    state.set("schedule_times", times)
    return times


def apply_add_channel(raw: str) -> list[str]:
    channels = parse_channel_list(raw)
    if not channels:
        raise ValueError("Укажите канал в формате @channel")
    data = state.load()
    current = data.setdefault("channels", [])
    for channel in channels:
        if channel not in current:
            current.append(channel)
    state.save(data)
    return current


def apply_remove_channel(raw: str) -> list[str]:
    channels = parse_channel_list(raw)
    if not channels:
        raise ValueError("Укажите канал в формате @channel")
    data = state.load()
    current = [item for item in data.get("channels", []) if item not in channels]
    data["channels"] = current
    state.save(data)
    return current


def apply_set_channels(raw: str) -> list[str]:
    channels = parse_channel_list(raw)
    if not channels:
        raise ValueError("Нужен хотя бы один канал.")
    state.set("channels", channels)
    return channels


def apply_set_test_channel(raw: str) -> str:
    channels = parse_channel_list(raw)
    if not channels:
        raise ValueError("Укажите тестовый канал в формате @channel")
    state.set("test_channel", channels[0])
    return channels[0]


def brief_to_dict(brief: EditorialBrief) -> dict[str, Any]:
    return {
        "signal": brief.signal.__dict__,
        "genre": brief.genre,
        "slot": brief.slot,
        "score": brief.score,
        "city": brief.city,
        "country": brief.country,
        "route_from": brief.route_from,
        "route_to": brief.route_to,
        "price": brief.price,
        "date_text": brief.date_text,
        "editorial_angle": brief.editorial_angle,
        "target_emotion": brief.target_emotion,
        "allowed_services": brief.allowed_services,
        "warnings": brief.warnings,
    }


def dict_to_brief(data: dict[str, Any]) -> EditorialBrief:
    signal = Signal(**data["signal"])
    payload = {key: value for key, value in data.items() if key != "signal"}
    return EditorialBrief(signal=signal, **payload)


def post_to_dict(post: GeneratedPost) -> dict[str, Any]:
    return {
        "decision": post.decision,
        "reject_reason": post.reject_reason,
        "genre": post.genre,
        "slot": post.slot,
        "editorial_angle": post.editorial_angle,
        "target_emotion": post.target_emotion,
        "media_query": post.media_query,
        "media_requirements": post.media_requirements,
        "best_variant_id": post.best_variant_id,
        "variants": [
            {
                **variant.__dict__,
                "buttons": [button.__dict__ for button in variant.buttons],
            }
            for variant in post.variants
        ],
    }


def dict_to_post(data: dict[str, Any]) -> GeneratedPost:
    variants: list[PostVariant] = []
    for item in data.get("variants", []):
        payload = dict(item)
        buttons = [Button(**button) for button in payload.pop("buttons", [])]
        variants.append(PostVariant(**payload, buttons=buttons))
    return GeneratedPost(
        decision=data.get("decision", "publishable"),
        reject_reason=data.get("reject_reason", ""),
        genre=data.get("genre", ""),
        slot=data.get("slot", ""),
        editorial_angle=data.get("editorial_angle", ""),
        target_emotion=data.get("target_emotion", ""),
        media_query=data.get("media_query", ""),
        media_requirements=data.get("media_requirements", ""),
        variants=variants,
        best_variant_id=int(data.get("best_variant_id", 1) or 1),
    )


def finalize_generated_post(brief: EditorialBrief, generated: GeneratedPost) -> tuple[PostVariant | None, list[str]]:
    for variant in generated.variants:
        polisher.polish(variant)
        engagement.improve_variant(brief, variant)
        cta.apply(brief, variant)
        for warning in fact_checker.review(brief, variant):
            if warning not in variant.warnings:
                variant.warnings.append(warning)
        duplicate_text, duplicate_reason = dedup.is_duplicate_text(f"{variant.title}\n{variant.body}\n{variant.cta_text}")
        if duplicate_text and duplicate_reason not in variant.warnings:
            variant.warnings.append(duplicate_reason)
            variant.score = max(0, int(variant.score or 0) - 30)
    best, selector_notes = quality.select_best(generated)
    if best:
        generated.best_variant_id = best.variant_id
    return best, selector_notes


def build_preview_header(brief: EditorialBrief) -> str:
    signal = brief.signal
    why = engagement.why_topic_now(brief)
    cta_hint = engagement.suggested_cta(brief)
    media_hint = engagement.media_hint(brief)
    return (
        "<b>Предпросмотр темы</b>\n"
        f"Источник: {html_escape(signal.source_name)}\n"
        f"Ссылка: {safe_source_link(signal)}\n"
        f"Жанр: <code>{html_escape(brief.genre)}</code>\n"
        f"Слот: <code>{html_escape(brief.slot)}</code>\n"
        f"Score темы: <code>{brief.score}/100</code>\n"
        f"Почему тема выбрана: {html_escape(why)}\n"
        f"Редакционный угол: {html_escape(brief.editorial_angle)}\n"
        f"CTA по логике: {html_escape(cta_hint)}\n"
        f"Требования к медиа: {html_escape(media_hint)}"
    )


def build_variant_preview(variant: PostVariant) -> str:
    parts = [
        f"<b>Вариант {variant.variant_id} — {html_escape(variant.style or 'редакционный')}</b>",
        post_writer.format_caption(variant),
    ]
    if variant.why_it_works:
        parts.append(f"<i>Почему работает:</i> {html_escape(variant.why_it_works)}")
    if variant.warnings:
        warnings = "\n".join(f"• {html_escape(item)}" for item in variant.warnings)
        parts.append(f"<i>Замечания:</i>\n{warnings}")
    parts.append(f"<i>Оценка: {variant.score}/100</i>")
    return "\n\n".join(part for part in parts if part)


def choose_best_variant_id(session: dict[str, Any], explicit_variant_id: int | None = None) -> int:
    if explicit_variant_id:
        return explicit_variant_id
    post = session.get("post", {})
    return int(post.get("best_variant_id", 1) or 1)


def record_publication(brief: EditorialBrief, variant: PostVariant, channels: list[str], mode: str) -> None:
    signal = brief.signal
    state.append_unique("published_urls", signal.url)
    state.append_unique("published_titles", variant.title)
    state.append_unique("published_text_hashes", hash_text(f"{variant.title}\n{variant.body}\n{variant.cta_text}"))
    state.append_unique("published_genres", brief.genre)
    state.append_unique("published_sources", signal.source_key)
    if brief.country:
        state.append_unique("published_countries", brief.country)
    if brief.city or brief.route_to:
        state.append_unique("published_cities", brief.city or brief.route_to)
    state.remember_source_pick(signal.source_key, signal.url, signal.title)
    state.append_json_list(
        "publication_log.json",
        {
            "mode": mode,
            "title": variant.title,
            "genre": brief.genre,
            "source_name": signal.source_name,
            "source_key": signal.source_key,
            "source_url": signal.url or signal.source_url,
            "channels": channels,
        },
        limit=500,
    )
    analytics.record_publication(
        {
            "mode": mode,
            "genre": brief.genre,
            "source": signal.source_key,
            "source_name": signal.source_name,
            "title": variant.title,
            "channels": channels,
        }
    )


def build_session_meta(brief: EditorialBrief, selector_notes: list[str]) -> dict[str, Any]:
    return {
        "why_topic_now": engagement.why_topic_now(brief),
        "suggested_cta": engagement.suggested_cta(brief),
        "media_hint": engagement.media_hint(brief),
        "selector_notes": selector_notes,
    }


def store_session(session_id: str, brief: EditorialBrief, generated: GeneratedPost, selector_notes: list[str]) -> None:
    state.store_draft_session(
        session_id,
        {
            "brief": brief_to_dict(brief),
            "post": post_to_dict(generated),
            "meta": build_session_meta(brief, selector_notes),
        },
    )


def load_latest_session() -> tuple[str, dict[str, Any] | None]:
    session_id = state.latest_session_id()
    if not session_id:
        return "", None
    return session_id, state.get_draft_session(session_id)


def session_variant(session: dict[str, Any], variant_id: int) -> PostVariant | None:
    generated = dict_to_post(session["post"])
    return next((item for item in generated.variants if item.variant_id == variant_id), None)


def select_signal_for_test(argument: str = "") -> tuple[Signal | None, str]:
    candidates = sources.fetch_signals(limit_per_source=5, include_fallback=True)
    if not candidates:
        return None, ""

    valid_candidates: list[Signal] = []
    for signal in candidates:
        rejected, _ = is_rejected_signal(signal)
        if rejected:
            continue
        valid_candidates.append(signal)
    if not valid_candidates:
        return None, ""

    arg = (argument or "").strip().lower()
    if arg.isdigit():
        index = max(0, int(arg) - 1)
        return valid_candidates[index % len(valid_candidates)], ""

    if arg:
        filtered = [signal for signal in valid_candidates if classifier.classify(signal) == arg]
        if filtered:
            return filtered[0], arg
        return None, arg

    start = int(state.get("test_cursor", 0) or 0)
    if TOPICS_ORDER:
        for step in range(len(TOPICS_ORDER)):
            genre = TOPICS_ORDER[(start + step) % len(TOPICS_ORDER)]
            for signal in valid_candidates:
                if classifier.classify(signal) == genre:
                    state.set("test_cursor", (start + step + 1) % len(TOPICS_ORDER))
                    return signal, genre

    state.set("test_cursor", start + 1)
    return valid_candidates[start % len(valid_candidates)], ""


def validate_signal(signal: Signal) -> tuple[bool, str]:
    rejected, reason = is_rejected_signal(signal)
    if rejected:
        return False, reason
    ok, reason = guard.check(signal)
    if not ok:
        return False, reason
    duplicate, reason = dedup.is_duplicate_signal(signal)
    if duplicate:
        return False, reason
    return True, ""


def prepare_brief(signal: Signal) -> EditorialBrief:
    slot = rotation.current_slot()
    genre = classifier.classify(signal)
    score, warnings = scoring.score(signal, genre, slot)
    return brief_engine.build(signal, genre, slot, score, warnings)


def generate_editorial_package(brief: EditorialBrief, mode: str = "normal") -> tuple[GeneratedPost, PostVariant | None, list[str]]:
    generated = writer.generate(brief, mode=mode)
    best, selector_notes = finalize_generated_post(brief, generated)
    return generated, best, selector_notes


async def send_session_preview(
    update: Update,
    session_id: str,
    brief: EditorialBrief,
    generated: GeneratedPost,
    selector_notes: list[str],
    title: str = "Предпросмотр темы",
) -> None:
    message = update.effective_message
    await message.reply_text(
        build_preview_header(brief).replace("Предпросмотр темы", title),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    for variant in generated.variants:
        await message.reply_text(
            build_variant_preview(variant),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    if selector_notes:
        notes = "\n".join(f"• {html_escape(note)}" for note in selector_notes)
        await message.reply_text(
            f"<b>Внутренняя проверка качества</b>\n{notes}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    await message.reply_text("Выберите действие:", reply_markup=draft_keyboard(session_id))


async def build_and_send_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, argument: str = "") -> None:
    signal, requested_genre = select_signal_for_test(argument)
    if not signal:
        genre_hint = f" для жанра {requested_genre}" if requested_genre else ""
        await update.effective_message.reply_text(f"Не нашёл подходящую тему{genre_hint}.")
        return

    valid, reason = validate_signal(signal)
    if not valid:
        state.set("last_skip_reason", reason)
        await update.effective_message.reply_text(f"Тема пропущена редактором: {reason}")
        return

    brief = prepare_brief(signal)
    generated, _, selector_notes = generate_editorial_package(brief, mode="normal")
    if generated.decision != "publishable" or not generated.variants:
        await update.effective_message.reply_text(
            f"AI-редактор отклонил тему: {generated.reject_reason or 'варианты не собраны'}"
        )
        return

    session_id = state.new_session_id()
    store_session(session_id, brief, generated, selector_notes)
    await send_session_preview(update, session_id, brief, generated, selector_notes)


async def regenerate_session(
    update: Update,
    session_id: str,
    mode: str,
    label: str,
) -> None:
    session = state.get_draft_session(session_id)
    if not session:
        await update.effective_message.reply_text("Сессия не найдена. Запустите /test заново.")
        return

    brief = dict_to_brief(session["brief"])
    generated, _, selector_notes = generate_editorial_package(brief, mode=mode)
    if generated.decision != "publishable" or not generated.variants:
        await update.effective_message.reply_text(
            f"Не получилось собрать новые варианты: {generated.reject_reason or 'редактор забраковал тему'}"
        )
        return

    new_session_id = state.new_session_id()
    store_session(new_session_id, brief, generated, selector_notes)
    await update.effective_message.reply_text(f"{label}. Ниже новая редакторская сессия.")
    await send_session_preview(update, new_session_id, brief, generated, selector_notes, title="Новая версия темы")


async def publish_session_variant(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session_id: str,
    variant_id: int | None = None,
    manual_mode: bool = True,
) -> None:
    session = state.get_draft_session(session_id)
    if not session:
        await update.effective_message.reply_text("Сессия не найдена. Запустите /test заново.")
        return

    brief = dict_to_brief(session["brief"])
    generated = dict_to_post(session["post"])
    selected_id = choose_best_variant_id(session, variant_id)
    variant = next((item for item in generated.variants if item.variant_id == selected_id), None)
    if not variant:
        await update.effective_message.reply_text("Не нашёл нужный вариант для публикации.")
        return
    if variant.score < QUALITY_MIN_PUBLICATION_SCORE:
        await update.effective_message.reply_text(
            f"Вариант {variant.variant_id} не проходит quality gate: {variant.score}/100. "
            "Используйте /rewrite, /softer или /sales."
        )
        return

    duplicate, duplicate_reason = dedup.is_duplicate_text(f"{variant.title}\n{variant.body}\n{variant.cta_text}")
    if duplicate:
        await update.effective_message.reply_text(f"Публикация остановлена: {duplicate_reason}")
        return

    channels = manual_target_channels() if manual_mode else autopost_target_channels()
    if not channels:
        await update.effective_message.reply_text(
            "Не задан целевой канал. Укажите тестовый канал через /set_test_channel @channel "
            "или основной список через /add_channel."
        )
        return

    media = media_engine.choose_media(brief, variant, generated.media_query)
    publisher = Publisher(context.application.bot)
    for channel in channels:
        await publisher.publish_to_channel(channel, variant, media)

    record_publication(brief, variant, channels, "manual" if manual_mode else "autopost")
    await update.effective_message.reply_text(
        f"Опубликовано в {len(channels)} канал(а/ов): <b>{html_escape(variant.title)}</b>",
        parse_mode=ParseMode.HTML,
    )


async def reject_session(update: Update, session_id: str) -> None:
    session = state.get_draft_session(session_id)
    if not session:
        await update.effective_message.reply_text("Сессия не найдена.")
        return
    brief = dict_to_brief(session["brief"])
    remember_rejected_signal(brief.signal, "Тема отклонена вручную из редакторской сессии.")
    await update.effective_message.reply_text("Тема отклонена и занесена в стоп-лист.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"<b>{PROJECT_NAME}</b>\n"
        f"Версия: <code>{VERSION}</code>\n\n"
        "Это AI-редакция travel-канала: она ищет тему, собирает 3 варианта поста, "
        "сама оценивает качество и публикует лучший вариант.\n\n"
        "Главное меню ниже."
    )
    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu(),
        disable_web_page_preview=True,
    )


async def version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"<code>{VERSION}</code>", parse_mode=ParseMode.HTML)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = state.load()
    text = (
        "<b>Статус AI-редакции</b>\n"
        f"Автопостинг: {'включён' if data.get('autopost_enabled') else 'выключен'}\n"
        f"Расписание: <code>{', '.join(data.get('schedule_times', [])) or 'не задано'}</code>\n"
        f"Каналы публикации: <code>{', '.join(data.get('channels', [])) or 'не заданы'}</code>\n"
        f"Тестовый канал: <code>{data.get('test_channel') or 'не задан'}</code>\n"
        f"Последний пропуск: {html_escape(data.get('last_skip_reason', 'нет'))}\n"
        f"Последняя сессия: <code>{data.get('last_session_id') or 'нет'}</code>"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())


async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    times = state.get("schedule_times", [])
    text = (
        "<b>Расписание автопостинга</b>\n"
        f"Сейчас: <code>{', '.join(times) or 'не задано'}</code>\n\n"
        "Можно изменить прямо из меню или командой:\n"
        "<code>/schedule_set 09:00,14:00,19:00</code>"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=schedule_menu())


async def schedule_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    try:
        times = apply_schedule(" ".join(context.args))
        scheduler.reschedule(times, lambda: context.application.create_task(run_autopost(context.application.bot)))
        await update.effective_message.reply_text(f"Расписание обновлено: {', '.join(times)}")
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))


async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = state.load()
    text = (
        "<b>Каналы публикации</b>\n"
        f"Основные каналы: <code>{', '.join(data.get('channels', [])) or 'не заданы'}</code>\n"
        f"Тестовый канал: <code>{data.get('test_channel') or 'не задан'}</code>\n\n"
        "Из меню можно добавить канал, заменить весь список или сменить тестовый канал.\n"
        "Также доступны команды /add_channel, /remove_channel, /set_channels, /set_test_channel."
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=channels_menu())


async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    try:
        channels = apply_add_channel(" ".join(context.args))
        await update.effective_message.reply_text(f"Канал добавлен. Сейчас: {', '.join(channels)}")
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))


async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    try:
        channels = apply_remove_channel(" ".join(context.args))
        await update.effective_message.reply_text(f"Список обновлён: {', '.join(channels) or 'пусто'}")
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))


async def set_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    try:
        channels = apply_set_channels(" ".join(context.args))
        await update.effective_message.reply_text(f"Список каналов заменён: {', '.join(channels)}")
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))


async def set_test_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    try:
        channel = apply_set_test_channel(" ".join(context.args))
        await update.effective_message.reply_text(f"Тестовый канал обновлён: {channel}")
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))


async def autopost_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state.set("autopost_enabled", True)
    scheduler.reschedule(
        state.get("schedule_times", []),
        lambda: context.application.create_task(run_autopost(context.application.bot)),
    )
    await update.effective_message.reply_text("Автопостинг включён.")


async def autopost_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state.set("autopost_enabled", False)
    await update.effective_message.reply_text("Автопостинг выключен.")


async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = [f"• {html_escape(item['name'])} — {html_escape(item['url'])}" for item in sources.list_sources()]
    await update.effective_message.reply_text(
        "<b>Источники тем</b>\n" + "\n".join(lines[:50]),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def list_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services = read_json("services.json", [])
    lines = [f"• {html_escape(item['name'])} ({html_escape(item['key'])}) — {html_escape(item['url'])}" for item in services]
    await update.effective_message.reply_text(
        "<b>Сервисы и реферальные ссылки</b>\n" + "\n".join(lines[:60]),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def list_topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = [f"• <code>{html_escape(item)}</code>" for item in TOPICS_ORDER]
    await update.effective_message.reply_text(
        "<b>Порядок тем для тестов</b>\n" + "\n".join(lines),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    await build_and_send_preview(update, context, " ".join(context.args).strip())


async def preview_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await test_cmd(update, context)


async def rewrite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    session_id, session = load_latest_session()
    if not session:
        await update.effective_message.reply_text("Нет активной редакторской сессии. Сначала запустите /test.")
        return
    await regenerate_session(update, session_id, "normal", "Переписал тему")


async def softer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    session_id, session = load_latest_session()
    if not session:
        await update.effective_message.reply_text("Нет активной редакторской сессии. Сначала запустите /test.")
        return
    await regenerate_session(update, session_id, "softer", "Сделал подачу мягче")


async def sales_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    session_id, session = load_latest_session()
    if not session:
        await update.effective_message.reply_text("Нет активной редакторской сессии. Сначала запустите /test.")
        return
    await regenerate_session(update, session_id, "sales", "Сделал подачу более коммерческой")


async def publish_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    session_id, session = load_latest_session()
    if not session:
        await update.effective_message.reply_text("Нет сессии для публикации. Сначала запустите /test.")
        return
    variant_id = None
    if context.args and str(context.args[0]).isdigit():
        variant_id = int(context.args[0])
    await publish_session_variant(update, context, session_id, variant_id=variant_id, manual_mode=True)


async def reject_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    session_id, session = load_latest_session()
    if not session:
        await update.effective_message.reply_text("Нет активной сессии для отклонения.")
        return
    await reject_session(update, session_id)


async def run_once(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    result = await run_autopost(context.application.bot, force=True)
    await update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


async def run_autopost(bot, force: bool = False) -> str:
    if not force and not state.get("autopost_enabled", False):
        return "Автопостинг выключен."

    channels = autopost_target_channels()
    if not channels:
        state.set("last_skip_reason", "Не заданы каналы автопубликации.")
        return "Публикация не выполнена: не заданы каналы."

    signals = sources.fetch_signals(limit_per_source=3, include_fallback=False)
    last_reason = "Нет сигналов."

    for signal in signals[:120]:
        valid, reason = validate_signal(signal)
        if not valid:
            last_reason = reason
            continue

        brief = prepare_brief(signal)
        if brief.score < AUTOPOST_MIN_LOCAL_SCORE:
            last_reason = f"Низкий локальный score темы: {brief.score}/100."
            continue

        rotation_ok, rotation_reason = rotation.allowed(
            brief.genre,
            brief.city or brief.route_to,
            brief.country,
            signal.source_key,
        )
        if not rotation_ok:
            last_reason = rotation_reason
            continue

        try:
            generated, best, selector_notes = generate_editorial_package(brief, mode="normal")
        except Exception as exc:
            last_reason = str(exc)
            log.warning("autopost generation failed: %s", exc)
            continue

        if generated.decision != "publishable" or not generated.variants:
            last_reason = generated.reject_reason or "AI-редактор не собрал publishable-варианты."
            continue
        if not best:
            last_reason = "AI не смог выбрать лучший вариант."
            continue
        if best.score < QUALITY_MIN_PUBLICATION_SCORE:
            last_reason = (
                f"Лучший вариант набрал только {best.score}/100 при минимуме "
                f"{QUALITY_MIN_PUBLICATION_SCORE}/100."
            )
            continue

        duplicate_text, duplicate_reason = dedup.is_duplicate_text(f"{best.title}\n{best.body}\n{best.cta_text}")
        if duplicate_text:
            last_reason = duplicate_reason
            continue

        media = media_engine.choose_media(brief, best, generated.media_query)
        publisher = Publisher(bot)
        for channel in channels:
            await publisher.publish_to_channel(channel, best, media)

        record_publication(brief, best, channels, "autopost")
        store_session(state.new_session_id(), brief, generated, selector_notes)
        return f"Опубликовано: <b>{html_escape(best.title)}</b>"

    state.set("last_skip_reason", last_reason)
    return f"Публикация не выполнена. Причина: {html_escape(last_reason)}"


async def handle_pending_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    action = context.user_data.get(PENDING_ACTION_KEY)
    if not action:
        return False

    raw = (update.effective_message.text or "").strip()
    try:
        if action == "schedule_set":
            times = apply_schedule(raw)
            scheduler.reschedule(
                times,
                lambda: context.application.create_task(run_autopost(context.application.bot)),
            )
            await update.effective_message.reply_text(f"Расписание обновлено: {', '.join(times)}")
        elif action == "add_channel":
            channels = apply_add_channel(raw)
            await update.effective_message.reply_text(f"Канал добавлен. Сейчас: {', '.join(channels)}")
        elif action == "set_channels":
            channels = apply_set_channels(raw)
            await update.effective_message.reply_text(f"Список каналов заменён: {', '.join(channels)}")
        elif action == "set_test_channel":
            channel = apply_set_test_channel(raw)
            await update.effective_message.reply_text(f"Тестовый канал обновлён: {channel}")
        else:
            return False
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))
    finally:
        context.user_data.pop(PENDING_ACTION_KEY, None)
    return True


async def text_test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    if await handle_pending_action(update, context):
        return
    text = (update.effective_message.text or "").strip()
    match = re.match(r"^(?:тест|test)\s*(\d+|[a-z_]+)?$", text, re.IGNORECASE)
    if match:
        await build_and_send_preview(update, context, match.group(1) or "")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not admin_only(update):
        return
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "menu:test":
        await query.message.reply_text("Запускаю редакторский тест...")
        await build_and_send_preview(update, context, "")
        return

    if data == "menu:status":
        await status(update, context)
        return

    if data == "menu:schedule":
        await query.edit_message_text(
            "<b>Расписание автопостинга</b>\n"
            f"Сейчас: <code>{', '.join(state.get('schedule_times', [])) or 'не задано'}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=schedule_menu(),
        )
        return

    if data == "menu:channels":
        await query.edit_message_text(
            "<b>Каналы публикации</b>\n"
            f"Основные: <code>{', '.join(state.get('channels', [])) or 'не заданы'}</code>\n"
            f"Тестовый: <code>{state.get('test_channel') or 'не задан'}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=channels_menu(),
        )
        return

    if data == "menu:edit_schedule":
        context.user_data[PENDING_ACTION_KEY] = "schedule_set"
        await query.message.reply_text("Отправьте новое расписание в формате: 09:00,14:00,19:00")
        return

    if data == "menu:add_channel":
        context.user_data[PENDING_ACTION_KEY] = "add_channel"
        await query.message.reply_text("Отправьте канал для добавления, например: @NadoTurKrd")
        return

    if data == "menu:set_channels":
        context.user_data[PENDING_ACTION_KEY] = "set_channels"
        await query.message.reply_text("Отправьте полный список каналов через запятую: @ch1,@ch2")
        return

    if data == "menu:set_test_channel":
        context.user_data[PENDING_ACTION_KEY] = "set_test_channel"
        await query.message.reply_text("Отправьте тестовый канал: @channel")
        return

    if data == "menu:back":
        await query.edit_message_text(
            f"<b>{PROJECT_NAME}</b>\nВерсия: <code>{VERSION}</code>\n\nГлавное меню.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu(),
        )
        return

    if data == "menu:autopost_on":
        state.set("autopost_enabled", True)
        scheduler.reschedule(
            state.get("schedule_times", []),
            lambda: context.application.create_task(run_autopost(context.application.bot)),
        )
        await query.edit_message_text("Автопостинг включён.", reply_markup=main_menu())
        return

    if data == "menu:autopost_off":
        state.set("autopost_enabled", False)
        await query.edit_message_text("Автопостинг выключен.", reply_markup=main_menu())
        return

    if data.startswith("pub:"):
        _, session_id, variant_id = data.split(":")
        await publish_session_variant(update, context, session_id, int(variant_id), manual_mode=True)
        return

    if data.startswith("regen:"):
        _, session_id, mode = data.split(":")
        label = {"normal": "Переписал тему", "softer": "Сделал подачу мягче", "sales": "Сделал подачу более коммерческой"}.get(mode, "Перегенерировал тему")
        await regenerate_session(update, session_id, mode, label)
        return

    if data.startswith("reject:"):
        _, session_id = data.split(":")
        await reject_session(update, session_id)
        return


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Telegram error", exc_info=context.error)


async def post_init(app: Application) -> None:
    scheduler.start()
    scheduler.reschedule(
        state.get("schedule_times", []),
        lambda: app.create_task(run_autopost(app.bot)),
    )
    log.info("Autopost schedule loaded: %s", ", ".join(state.get("schedule_times", [])))


async def post_shutdown(app: Application) -> None:
    scheduler.shutdown()


def main() -> None:
    ensure_dirs()
    token = env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")

    app = Application.builder().token(token).post_init(post_init).post_shutdown(post_shutdown).build()
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CommandHandler("version", version))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CommandHandler("preview", preview_cmd))
    app.add_handler(CommandHandler("rewrite", rewrite_cmd))
    app.add_handler(CommandHandler("softer", softer_cmd))
    app.add_handler(CommandHandler("sales", sales_cmd))
    app.add_handler(CommandHandler("publish", publish_cmd))
    app.add_handler(CommandHandler("reject", reject_cmd))
    app.add_handler(CommandHandler("run_once", run_once))
    app.add_handler(CommandHandler("schedule", schedule_cmd))
    app.add_handler(CommandHandler("schedule_set", schedule_set))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("set_channels", set_channels))
    app.add_handler(CommandHandler("set_test_channel", set_test_channel))
    app.add_handler(CommandHandler("autopost_on", autopost_on))
    app.add_handler(CommandHandler("autopost_off", autopost_off))
    app.add_handler(CommandHandler("sources", list_sources))
    app.add_handler(CommandHandler("services", list_services))
    app.add_handler(CommandHandler("topics", list_topics))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_test_handler))
    app.add_error_handler(error_handler)
    log.info("Starting %s", VERSION)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
