# Мир на ладони — AI Newsroom Bot v5.0

Чистая финальная архитектура Telegram-бота AI-редактора по MASTER-ТЗ.

## Запуск на Railway

Start command:

```bash
python -m src.telegram_app
```

## Ключевой принцип

Бот не копирует источники. Источник — только сырьё для редакционного повода. Итог — готовый Telegram-пост: заголовок, короткие абзацы, вовлечение, уместные ссылки, релевантное медиа.

## Главные команды

- `/menu` — главное меню
- `/version` — версия
- `/test` — следующий тестовый пост
- `/test 1` или сообщение `тест 1` — тест темы под номером 1
- `/test flight_deal` — тест жанра
- `/run_once` — один автопостинг вручную
- `/schedule` — расписание
- `/schedule_set 09:00,14:00,19:00` — сменить расписание
- `/channels` — список каналов
- `/add_channel @channel` — добавить канал
- `/remove_channel @channel` — удалить канал
- `/set_channels @channel1,@channel2` — заменить список каналов
- `/autopost_on` / `/autopost_off` — автопостинг
- `/status` — статус

## Проверка проекта

```bash
python tests/validate_project.py
```
