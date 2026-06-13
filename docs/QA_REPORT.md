# QA-отчёт v6.2

## Выполненная проверка

```bash
python -m compileall -q src tests
python tests/validate_project.py
python tests/test_rotation.py
python tests/test_cta_rules.py
python tests/test_media_policy.py
python tests/test_publish_split.py
python tests/test_pipeline_dryrun.py
```

## Результат

- Синтаксис `src/*.py` и `tests/*.py`: OK.
- Структура проекта: OK.
- JSON-конфиги: OK.
- `.env.example`: OK.
- Новые источники из ТЗ: OK.
- TourJin: OK.
- CTA rules: OK.
- Медиа fallback/generation: OK.
- Split длинного поста с фото: OK.
- Pipeline dry-run без Telegram/OpenAI: OK.
- `__pycache__` и `.pyc` удалены перед упаковкой: OK.

## Что нельзя проверить без реальных ключей и Railway

- Реальную публикацию в Telegram-канал.
- Реальный ответ OpenAI API.
- Реальный поиск Pexels/Unsplash/Pixabay.
- Реальную стабильность Telegram в РФ.
- Права бота в канале.

Для этого после деплоя нужно выполнить `/version`, `/status`, `/test 1`, `/test 2`, `/test 3`, `/run_once`.
