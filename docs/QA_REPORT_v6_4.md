# QA REPORT v6.4

Проверки выполнены локально перед упаковкой:

- python tests/validate_project.py
- python tests/test_master_prompt_contract.py
- python tests/test_menu_contract.py
- python tests/test_openai_required.py
- python tests/test_cta_rules.py
- python tests/test_media_policy.py
- python tests/test_publish_split.py
- python tests/test_rotation.py
- python tests/test_pipeline_dryrun.py
- python -m compileall -q src tests
- повторный validate_project.py после удаления __pycache__ и *.pyc

Результат: OK.

Ключевые изменения v6.4:

- один master prompt для OpenAI: prompts/master_writer_ru.md;
- AIWriter использует только master_writer_ru.md;
- локальный fallback-генератор удалён из AIWriter и не используется;
- /test генерирует один лучший пост и каждый раз берёт новую тему;
- preview_history учитывается в дедупликации, поэтому непринятые тестовые темы не повторяются сразу;
- меню управления сделано кнопками;
- добавлены кнопки теста, онлайн-публикации, расписания, добавления/замены каналов;
- после генерации и публикации бот отдаёт полный отчёт: генератор, модель, промт, brief, качество, причины оценки, медиа, кнопки, публикация;
- оценка качества считается кодом, а не берётся из ответа OpenAI;
- если OpenAI не отвечает, пост не генерируется и не публикуется.
