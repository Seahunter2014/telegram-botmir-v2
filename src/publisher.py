from __future__ import annotations
from pathlib import Path
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def keyboard(buttons:list[dict])->InlineKeyboardMarkup|None:
    rows=[[InlineKeyboardButton(b['text'], url=b['url'])] for b in buttons[:3] if b.get('text') and b.get('url')]
    return InlineKeyboardMarkup(rows) if rows else None

def render_post(v:dict)->str:
    return '\n\n'.join([x.strip() for x in [v.get('title',''),v.get('text',''),v.get('cta','')] if x and x.strip()])[:3900]

async def publish_to_channel(bot:Any, channel_id:str, variant:dict, media:dict)->bool:
    used=False
    if media.get('type')=='url' and media.get('value'):
        await bot.send_photo(chat_id=channel_id, photo=media['value']); used=True
    elif media.get('type')=='file' and media.get('value') and Path(media['value']).exists():
        with Path(media['value']).open('rb') as fh: await bot.send_photo(chat_id=channel_id, photo=fh)
        used=True
    await bot.send_message(chat_id=channel_id, text=render_post(variant), reply_markup=keyboard(variant.get('buttons',[])), disable_web_page_preview=False)
    return used
