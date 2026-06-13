from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    app = (Path(__file__).resolve().parents[1] / "src" / "telegram_app.py").read_text(encoding="utf-8")
    menu = (Path(__file__).resolve().parents[1] / "src" / "menu.py").read_text(encoding="utf-8")
    assert "⭐ Оценить пост" in menu, "нет кнопки оценки"
    assert "rate_cmd" in app and 'callback_data=f"rate:{post_id}:{i}"' in app, "нет команды/кнопок рейтинга"
    assert "record_post_rating" in (Path(__file__).resolve().parents[1] / "src" / "state_store.py").read_text(encoding="utf-8"), "нет сохранения рейтинга"
    print("OK: rating contract")

if __name__ == "__main__":
    main()
