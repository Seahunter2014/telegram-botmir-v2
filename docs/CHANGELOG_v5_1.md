# CHANGELOG v5.1 — SCHEDULER_EVENT_LOOP_FIX

Исправлена критическая ошибка запуска Railway:

```text
RuntimeError: no running event loop
```

Причина:
`AsyncIOScheduler.start()` вызывался в `main()` до того, как `python-telegram-bot` создавал рабочий asyncio event loop.

Исправление:
- запуск scheduler перенесён в `post_init(app)`;
- shutdown scheduler перенесён в `post_shutdown(app)`;
- автопостинг создаёт task через `app.create_task(...)`;
- `src/scheduler.py` получил безопасный `shutdown()` и защитные параметры jobs.

Проверка:
- `src/*.py` компилируются;
- `configs/*.json` читаются;
- `tests/validate_project.py` проходит успешно.
