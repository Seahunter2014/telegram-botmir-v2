# Telegram-бот AI-редактор «Мир на ладони»

Версия: **2026.06.05 FINAL AI NEWSROOM**

Чистая финальная сборка без старых шаблонных генераторов. Бот работает как AI-редакция: ищет темы, классифицирует жанр, делает редакционный план, генерирует 3 варианта поста, проверяет шаблонность, выбирает CTA, подбирает медиа и публикует в Telegram.

## Railway Start Command

```bash
python -m src.telegram_app
```

## Обязательные переменные Railway

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_ID=
TELEGRAM_CHANNEL_ID=
TEST_CHANNEL_ID=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TEMPERATURE=0.85
PEXELS_API_KEY=
TRAVELPAYOUTS_API_TOKEN=
TRAVELPAYOUTS_MARKER=98526
```

## Проверка перед загрузкой

```bash
python tests/validate_project.py
```

## Команды

- `/version`
- `/test`
- `/preview`
- `/publish`
- `/autopost_on`
- `/autopost_off`
- `/schedule`
- `/status`
- `/last`
- `/why_skipped`
- `/sources`
- `/topics`
- `/services`
