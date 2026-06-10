from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("/test"), KeyboardButton("/run_once")],
        [KeyboardButton("/status"), KeyboardButton("/schedule")],
        [KeyboardButton("/autopost_on"), KeyboardButton("/autopost_off")],
        [KeyboardButton("/channels"), KeyboardButton("/sources")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)
