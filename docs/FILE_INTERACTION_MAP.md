# Карта взаимодействия файлов

1. `telegram_app.py` принимает команды Telegram и управляет сценарием.
2. `source_manager.py` получает сигналы из источников.
3. `topic_guard.py` отбрасывает мусорные темы.
4. `topic_classifier.py` определяет жанр.
5. `scoring_engine.py` ставит score теме.
6. `rotation_engine.py` проверяет ротацию жанров/источников/городов.
7. `dedup_engine.py` защищает от повторов.
8. `editorial_brief_engine.py` собирает редакционное задание.
9. `ai_writer.py` отправляет brief в OpenAI и получает 3 варианта.
10. `editorial_polisher.py` чистит формат.
11. `quality_selector.py` оценивает варианты и выбирает лучший.
12. `cta_engine.py` пересобирает кнопки по смыслу.
13. `media_engine.py` подбирает фото или карточку.
14. `publisher.py` публикует фото+caption+кнопки в один или несколько каналов.
15. `state_store.py` хранит расписание, каналы, историю, draft-сессии.
16. `scheduler.py` запускает автопостинг по расписанию.
