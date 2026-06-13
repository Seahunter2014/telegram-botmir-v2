from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    text = (ROOT / "src" / "menu.py").read_text(encoding="utf-8")
    for label in ["🧪 Тест поста", "🚀 Опубликовать онлайн", "✏️ Заменить расписание", "➕ Добавить канал", "🔁 Заменить каналы"]:
        assert label in text, f"нет кнопки {label}"
    app = (ROOT / "src" / "telegram_app.py").read_text(encoding="utf-8")
    assert "menu_text_handler" in app, "нет обработчика текстовых кнопок"
    print("OK: menu contract")

if __name__ == "__main__": main()
