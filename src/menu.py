from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Тест поста", callback_data="menu:test"), InlineKeyboardButton("📌 Статус", callback_data="menu:status")],
        [InlineKeyboardButton("⏰ Расписание", callback_data="menu:schedule"), InlineKeyboardButton("📣 Каналы", callback_data="menu:channels")],
        [InlineKeyboardButton("▶️ Автопостинг", callback_data="menu:autopost_on"), InlineKeyboardButton("⏸ Выключить", callback_data="menu:autopost_off")],
    ])


def draft_keyboard(session_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Опубликовать 1", callback_data=f"pub:{session_id}:1")],
        [InlineKeyboardButton("✅ Опубликовать 2", callback_data=f"pub:{session_id}:2")],
        [InlineKeyboardButton("✅ Опубликовать 3", callback_data=f"pub:{session_id}:3")],
        [InlineKeyboardButton("🔁 Переписать", callback_data=f"regen:{session_id}:normal"), InlineKeyboardButton("🤍 Мягче", callback_data=f"regen:{session_id}:softer")],
        [InlineKeyboardButton("💰 Продающе", callback_data=f"regen:{session_id}:sales"), InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{session_id}")],
    ])
