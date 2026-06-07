# v5.3 — GPT_OUTPUT_NORMALIZE_FIX

Исправлена ошибка ручного теста:

```text
Ошибка теста: 'str' object has no attribute 'extend'
```

Причина: OpenAI иногда возвращал `warnings` строкой вместо массива.
Код ожидал список и вызывал `.extend()`, из-за чего `/test` падал.

Исправлены файлы:

- `src/ai_writer.py` — нормализация полей `warnings`, `buttons`, `variants`, текстовых и числовых полей.
- `src/quality_selector.py` — дополнительная защита перед `.extend()`.
- `src/version.py` — версия v5.3.

Проверка:

- Python compile: OK
- JSON configs: OK
- validate_project.py: OK
- synthetic GPT warnings as string: OK
- synthetic GPT buttons as invalid string: OK
