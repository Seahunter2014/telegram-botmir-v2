# Короткий чек-лист проекта

Полный чек-лист лежит в `docs/CHECKLIST_Mir_na_Ladoni_Bot_v6_2.md`.

- [ ] `python -m compileall -q src tests` проходит.
- [ ] `python tests/validate_project.py` проходит.
- [ ] Все JSON в `configs/` читаются.
- [ ] Все команды Telegram зарегистрированы.
- [ ] `/test 1`, `/test 2`, `/test 3` дают разные темы.
- [ ] `/run_once` публикует или даёт отчёт.
- [ ] Fallback работает, если источники недоступны.
- [ ] Длинный caption с фото делится на 2 части.
- [ ] Секретов в коде нет.
