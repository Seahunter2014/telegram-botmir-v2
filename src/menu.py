from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup

BTN_TEST = "🧪 Тест поста"
BTN_PUBLISH = "🚀 Опубликовать онлайн"
BTN_STATUS = "📊 Статус"
BTN_LAST = "🧾 Последний отчёт"
BTN_RATE = "⭐ Оценить пост"
BTN_SCHEDULE = "🕒 Расписание"
BTN_SET_SCHEDULE = "✏️ Заменить расписание"
BTN_CHANNELS = "📣 Каналы"
BTN_ADD_CHANNEL = "➕ Добавить канал"
BTN_SET_CHANNELS = "🔁 Заменить каналы"
BTN_AUTOP_ON = "✅ Автопостинг ON"
BTN_AUTOP_OFF = "⛔ Автопостинг OFF"
BTN_SOURCES = "🗂 Источники"
BTN_MENU = "🏠 Меню"


def main_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(BTN_TEST), KeyboardButton(BTN_PUBLISH)],
        [KeyboardButton(BTN_SCHEDULE), KeyboardButton(BTN_CHANNELS)],
        [KeyboardButton(BTN_SET_SCHEDULE), KeyboardButton(BTN_ADD_CHANNEL), KeyboardButton(BTN_SET_CHANNELS)],
        [KeyboardButton(BTN_STATUS), KeyboardButton(BTN_LAST), KeyboardButton(BTN_RATE)],
        [KeyboardButton(BTN_AUTOP_ON), KeyboardButton(BTN_AUTOP_OFF), KeyboardButton(BTN_SOURCES)],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)
