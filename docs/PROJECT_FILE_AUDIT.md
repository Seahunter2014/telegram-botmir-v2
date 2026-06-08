# PROJECT FILE AUDIT — AI Newsroom v5.0

Версия: `2026.06.07 FINAL AI NEWSROOM v5.0 MASTER_EDITORIAL_CORE`

## 1. Корневые файлы

| Файл | Что внутри | Связи |
|---|---|---|
| `README.md` | Инструкция запуска, команды, принцип работы | Используется админом при деплое |
| `requirements.txt` | Только Python-библиотеки | Railway устанавливает зависимости |
| `.env.example` | Пример переменных Railway | Не содержит секретов |

## 2. `src/` — runtime-код

| Файл | Назначение | Вход | Выход / связь |
|---|---|---|---|
| `telegram_app.py` | Главный Telegram runtime: команды, меню, тесты, публикации, автопостинг | Telegram updates, callback buttons | Вызывает все редакционные модули |
| `version.py` | Версия проекта | — | `/version`, логи |
| `config_loader.py` | Загрузка env, JSON и prompts | `.env`, Railway ENV, `configs/`, `prompts/` | Используется всеми модулями |
| `models.py` | Dataclass-модели: Signal, Brief, PostVariant, GeneratedPost | — | Единый контракт между модулями |
| `state_store.py` | Хранит расписание, каналы, историю, draft-сессии | `data/state.json`, ENV | Данные для scheduler, dedup, rotation, publisher |
| `source_manager.py` | Обходит источники и получает сигналы | `configs/sources.json` | Список `Signal` |
| `signal_extractor.py` | Извлекает маршрут, дату, цену | `Signal.text` | route_from, route_to, price, date_text |
| `topic_guard.py` | Фильтр мусорных тем | `Signal` | allow/reject + причина |
| `topic_classifier.py` | Определяет жанр | `Signal` | genre |
| `scoring_engine.py` | Оценивает тему | `Signal`, genre, slot | score + warnings |
| `rotation_engine.py` | Не даёт повторять жанры/города/источники подряд | `state.json` | allow/reject |
| `dedup_engine.py` | Защита от повторов URL, заголовка, текста | `state.json`, `Signal`, text | duplicate true/false |
| `editorial_brief_engine.py` | Собирает редакционное задание для GPT | Signal + genre + score | `EditorialBrief` |
| `openai_client.py` | Вызов OpenAI JSON mode | prompts + brief | JSON-ответ модели |
| `ai_writer.py` | Главный AI-генератор 3 вариантов | `EditorialBrief`, prompts | `GeneratedPost` |
| `json_repair.py` | Безопасное извлечение JSON из ответа | raw GPT text | dict |
| `anti_template_checker.py` | Проверка запрещённых фраз и технических маркеров | title/body/cta | errors |
| `editorial_polisher.py` | Локальная чистка форматирования | `PostVariant` | cleaned `PostVariant` |
| `quality_selector.py` | Локальная оценка вариантов и выбор лучшего | `GeneratedPost` | best variant |
| `cta_engine.py` | Пересобирает кнопки по смыслу жанра | `EditorialBrief`, `PostVariant` | variant.buttons |
| `url_builder.py` | Собирает deeplink Aviasales и берёт партнёрские ссылки | `services.json`, `cities_iata.json` | URL |
| `media_engine.py` | Источник фото / Pexels / fallback-card / offer-card | brief, variant | URL или путь к картинке |
| `telegram_post_writer.py` | Форматирует caption и preview | `PostVariant` | HTML caption |
| `publisher.py` | Публикует фото+caption+кнопки в канал | Bot, channel, variant, media | Telegram message |
| `scheduler.py` | Планировщик автопостинга | schedule_times | APScheduler jobs |
| `menu.py` | Inline-меню и кнопки выбора вариантов | — | InlineKeyboardMarkup |
| `analytics_store.py` | Запись факта публикации | publication payload | `state.analytics` |
| `text_utils.py` | Очистка текста, hash, цена, дата, HTML escape | text | normalized values |

## 3. `configs/` — редакционные данные

| Файл | Что внутри | Используется |
|---|---|---|
| `sources.json` | 15 источников: Vandrouki, Aviasales TG, Travelata TG, ПСЖР, TravelAsk, Tripster, Яндекс Путешествия, Горбилет, IMIGRATA, relocate_easy, ekspat_info, puteshe, Trip.com Activities, ptuxon | `source_manager.py` |
| `services.json` | Партнёрские сервисы и ссылки, включая обязательный `tourjin_bot` | `cta_engine.py`, `url_builder.py`, `/services` |
| `link_rules.json` | Правила CTA по жанрам | `cta_engine.py` |
| `topics.json` | Каталог жанров | документация, расширение логики |
| `forbidden_phrases.json` | Запрещённые фразы | `anti_template_checker.py`, `ai_writer.py` |
| `editorial_policy.json` | Политика канала и лимиты | документация / future use |
| `cities_iata.json` | IATA-коды для deeplink Aviasales | `url_builder.py`, `signal_extractor.py` |
| `city_aliases.json` | Нормализация городов | `signal_extractor.py` |
| `fallback_signals.json` | Тестовые темы для ручного режима при недоступных источниках | `source_manager.py` |

## 4. `prompts/` — мозг редакции

| Файл | Роль |
|---|---|
| `system_editor_ru.md` | Главная роль: бот — главный редактор Telegram travel-канала |
| `hook_engagement_engine_ru.md` | Крючки, заголовки, вовлечение, концовки |
| `writer_3_variants_ru.md` | Требование генерировать 3 самостоятельных варианта |
| `cta_rules_ru.md` | Уместность CTA и ссылок |
| `fact_check_ru.md` | Осторожные формулировки фактов |
| `editorial_planner_ru.md` | Логика редакционного planning |
| `anti_template_ru.md` | Антишаблонная проверка |
| `quality_selector_ru.md` | Критерии выбора лучшего варианта |

## 5. `data/` — состояние

| Файл | Назначение |
|---|---|
| `state.json` | Каналы, расписание, история, draft-сессии |
| `publication_log.json` | Зарезервировано под лог публикаций |
| `rejected_topics.json` | Зарезервировано под отклонённые темы |
| `analytics.json` | Зарезервировано под аналитику |

## 6. `tests/`

| Файл | Проверяет |
|---|---|
| `validate_project.py` | Структуру, JSON, компиляцию Python, отсутствие мусора, наличие TourJin, наличие меню расписания/каналов/тестов |

## 7. Проверенные сценарии в коде

- `/test` — следующая тема.
- `/test 1` — первая тема.
- Сообщение `тест 1` — первая тема без слэша.
- `/schedule` и `/schedule_set` — меню/смена расписания.
- `/channels`, `/add_channel`, `/remove_channel`, `/set_channels` — управление одним или несколькими каналами.
- `/autopost_on`, `/autopost_off` — управление автопостингом.
- `/run_once` — ручной запуск автопостинга.
- Публикация выбранного варианта в один или несколько каналов.
