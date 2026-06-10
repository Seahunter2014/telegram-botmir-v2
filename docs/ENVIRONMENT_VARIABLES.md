# Переменные окружения

| Переменная | Обязательна | Где используется | Назначение |
|---|---:|---|---|
| TELEGRAM_BOT_TOKEN | да | telegram_app.py | токен BotFather |
| TELEGRAM_ADMIN_ID | да | telegram_app.py | ID администратора |
| TELEGRAM_CHANNEL_ID | да | pipeline/publisher | основной канал |
| TEST_CHANNEL_ID | да | telegram_app.py | тестовый канал |
| TELEGRAM_CHANNEL_URL | нет | cta_engine.py | URL кнопки подписки/шеринга |
| OPENAI_API_KEY | желательно | openai_client.py | генерация AI-постов |
| OPENAI_MODEL | да | openai_client.py | модель OpenAI |
| OPENAI_TEMPERATURE | да | openai_client.py | температура генерации |
| LOCAL_WRITER_FALLBACK | да | ai_writer.py | локальный fallback при сбое OpenAI |
| PEXELS_API_KEY | нет | media_sources.py | поиск фото |
| UNSPLASH_ACCESS_KEY | нет | media_sources.py | поиск фото |
| PIXABAY_API_KEY | нет | media_sources.py | поиск фото |
| TRAVELPAYOUTS_API_TOKEN | нет | future integrations | API Travelpayouts |
| TRAVELPAYOUTS_MARKER | нет | future integrations | marker |
| SCHEDULE_TIMEZONE | да | scheduler.py | таймзона расписания |
| ALLOW_FALLBACK_AUTOPUBLISH | да | pipeline.py | fallback-темы при сбоях источников |
