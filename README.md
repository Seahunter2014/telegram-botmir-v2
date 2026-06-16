# Мир на ладони — AI-редакция travel Telegram-канала

Версия: `2026.06.16 AI REDAKTOR BOT FINAL — ASYNC AUTOPUBLISH, UNIQUE TOPICS, SINGLE REWRITE, RATINGS MEMORY`.

Бот работает как AI-редакция: ищет travel-сигналы, фильтрует мусор, выбирает тему, генерирует пост через OpenAI, переписывает его до прохода Quality Gate, проверяет качество, подбирает CTA/кнопки/медиа, публикует в канал и пишет диагностический отчёт.

## Запуск на Railway

Start Command:

```bash
python -m src.telegram_app
```

Обязательные переменные:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_ID=
TELEGRAM_CHANNEL_ID=
TEST_CHANNEL_ID=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1
OPENAI_TEMPERATURE=0.85
SCHEDULE_TIMEZONE=Europe/Moscow
ALLOW_FALLBACK_AUTOPUBLISH=true
```

Pexels/Unsplash/Pixabay необязательны: если фото не найдено, бот создаёт локальный travel-визуал.

## Команды

- `/start`, `/menu`
- `/version`
- `/status`
- `/test`, `/test 1`, `/test 2`, `/test 3`
- `/run_once`
- `/autopost_on`, `/autopost_off`
- `/schedule`, `/schedule_set 09:00,14:00,19:00`
- `/channels`, `/add_channel`, `/remove_channel`, `/set_channels`
- `/sources`, `/services`, `/topics`
- `/rate НОМЕР_ПОСТА ОЦЕНКА_1_10` — оценить любой опубликованный пост
- `/why_skipped`, `/last`

## Локальная проверка

```bash
python -m compileall -q src tests
python tests/validate_project.py
python tests/test_rotation.py
python tests/test_cta_rules.py
python tests/test_media_policy.py
python tests/test_publish_split.py
python tests/test_pipeline_dryrun.py
```

## Важное

Секреты не хранятся в коде. Все токены задаются только через переменные окружения Railway.
