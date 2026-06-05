from __future__ import annotations
from pathlib import Path
from typing import Any
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

CAPTION_LIMIT = 1000
MESSAGE_LIMIT = 3900

GENRE_EMOJI = {
    'flight_deal': '✈️',
    'tour_offer': '🔥',
    'hot_tour': '🔥',
    'last_minute': '🔥',
    'hotel_post': '🏨',
    'premium_hotel': '🏨',
    'event_trip': '🎟',
    'concert_trip': '🎟',
    'weekend_activity': '🗺',
    'activities_post': '🎭',
    'destination_post': '🌍',
    'weekend_trip': '🧳',
    'city_break': '🏙',
    'practical_travel': '🧳',
    'visa_or_residence': '📌',
    'payment_abroad': '💳',
    'insurance_tip': '🛡',
}


def keyboard(buttons: list[dict]) -> InlineKeyboardMarkup | None:
    rows = []
    for b in buttons[:3]:
        text = str(b.get('text', '')).strip()
        url = str(b.get('url', '')).strip()
        if text and url:
            rows.append([InlineKeyboardButton(text, url=url)])
    return InlineKeyboardMarkup(rows) if rows else None


def _plain(v: dict) -> str:
    return '\n\n'.join([x.strip() for x in [v.get('title', ''), v.get('text', ''), v.get('cta', '')] if x and x.strip()])


def _truncate_html_body(text: str, limit: int) -> str:
    # Текст уже будет экранирован после обрезки, поэтому тут режем обычную строку.
    text = str(text or '').strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit('\n\n', 1)[0].strip()
    if len(cut) < 350:
        cut = text[:limit].rsplit(' ', 1)[0].strip()
    return cut.rstrip('.,;:') + '…'


def render_post(v: dict, topic: str | None = None, *, html: bool = True, for_caption: bool = False) -> str:
    """Готовит пост именно как Telegram-публикацию, а не как сырой текст.

    Формат по ТЗ:
    - заметный заголовок;
    - короткие абзацы;
    - умеренные эмодзи;
    - без служебных слов;
    - текст умещается в подпись к фото, если публикуется с медиа.
    """
    title = str(v.get('title', '')).strip()
    body = str(v.get('text', '')).strip()
    cta = str(v.get('cta', '')).strip()
    topic = topic or str(v.get('topic', '') or v.get('genre_key', '')).strip()
    emoji = str(v.get('emoji', '') or GENRE_EMOJI.get(topic, '🌍'))

    if for_caption:
        # Telegram photo caption ограничен. Лучше сильный компактный пост с фото, чем картинка отдельно и простыня ниже.
        reserve = len(title) + len(cta) + 24
        body = _truncate_html_body(body, max(360, CAPTION_LIMIT - reserve))

    if html:
        head = f"<b>{escape((emoji + ' ' + title).strip())}</b>" if title else ''
        parts = [head]
        if body:
            parts.append(escape(body))
        if cta:
            parts.append(escape(cta))
        result = '\n\n'.join([p for p in parts if p]).strip()
        if for_caption and len(result) > CAPTION_LIMIT:
            # Финальная страховка: не отдаём Telegram слишком длинный caption.
            result = result[:CAPTION_LIMIT - 1].rsplit(' ', 1)[0].strip() + '…'
        return result[:MESSAGE_LIMIT]

    return _plain(v)[:MESSAGE_LIMIT]


async def publish_to_channel(bot: Any, channel_id: str, variant: dict, media: dict, topic: str | None = None) -> bool:
    markup = keyboard(variant.get('buttons', []))
    if media.get('type') == 'url' and media.get('value'):
        await bot.send_photo(
            chat_id=channel_id,
            photo=media['value'],
            caption=render_post(variant, topic, html=True, for_caption=True),
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
        return True
    if media.get('type') == 'file' and media.get('value') and Path(media['value']).exists():
        with Path(media['value']).open('rb') as fh:
            await bot.send_photo(
                chat_id=channel_id,
                photo=fh,
                caption=render_post(variant, topic, html=True, for_caption=True),
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
            )
        return True

    await bot.send_message(
        chat_id=channel_id,
        text=render_post(variant, topic, html=True),
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
        disable_web_page_preview=False,
    )
    return False
