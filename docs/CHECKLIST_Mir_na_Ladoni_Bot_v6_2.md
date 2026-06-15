# ПОЛНЫЙ ЧЕК-ЛИСТ ПРОВЕРКИ КОМПЛЕКТА БОТА v6.2
## AI-редакция travel-канала «Мир на ладони»

Версия: **v6.2 FINAL BOT ACCEPTANCE CHECKLIST**  
Назначение: проверить не только наличие файлов, но и содержание, взаимодействие модулей, последовательность работы, устойчивость к сбоям, соответствие ТЗ и способность бота публиковать качественные посты.

---

# 1. Принцип проверки

Проект считается готовым не тогда, когда файлы есть и Python компилируется, а когда доказано, что бот проходит полный редакционный pipeline:

```text
источники
→ сигналы
→ фильтрация
→ fallback при необходимости
→ классификация
→ scoring
→ ротация
→ brief
→ GPT 3 варианта
→ engagement
→ fact-check
→ CTA
→ media
→ split длинного поста
→ publish
→ state
→ diagnostics
```

Каждая проверка имеет статус:

- **BLOCKER** — без исправления нельзя деплоить.
- **MAJOR** — можно запустить только для теста, но нельзя считать финальной версией.
- **MINOR** — не блокирует запуск, но снижает качество.

---

# 2. Проверка структуры проекта

## 2.1. Корень проекта

- [ ] **BLOCKER** В корне есть `requirements.txt`.
- [ ] **BLOCKER** В корне есть `README.md`.
- [ ] **BLOCKER** В корне есть `.env.example`.
- [ ] **BLOCKER** В корне нет старых `.py` файлов вне `src/`.
- [ ] **BLOCKER** В корне нет архивов внутри проекта.
- [ ] **BLOCKER** В корне нет папки `download`.
- [ ] **BLOCKER** В корне нет `__pycache__`.
- [ ] **BLOCKER** В корне нет `.pyc`.
- [ ] **MAJOR** Есть `docs/` с ТЗ, чек-листом и changelog.
- [ ] **MAJOR** Есть `tests/` с не только формальным validate, но и runtime/dry-run тестами.

Ожидаемая структура:

```text
telegram-botmir-v2/
├── src/
├── configs/
├── prompts/
├── data/
├── tests/
├── docs/
├── requirements.txt
├── README.md
└── .env.example
```

---

# 3. Проверка `requirements.txt`

- [ ] **BLOCKER** Файл содержит только библиотеки.
- [ ] **BLOCKER** Нет `TELEGRAM_BOT_TOKEN`.
- [ ] **BLOCKER** Нет `OPENAI_API_KEY`.
- [ ] **BLOCKER** Нет русских инструкций.
- [ ] **BLOCKER** Нет одной длинной строки вместо списка зависимостей.
- [ ] **BLOCKER** Есть `python-telegram-bot>=21.0`.
- [ ] **BLOCKER** Есть `openai>=1.30.0`.
- [ ] **BLOCKER** Есть `requests` или async HTTP-клиент.
- [ ] **BLOCKER** Есть `beautifulsoup4` / `lxml` для парсинга источников.
- [ ] **BLOCKER** Есть `apscheduler` для расписания.
- [ ] **MAJOR** Есть библиотека для изображений, если бот генерирует/обрабатывает картинки.

Команда проверки:

```bash
python -m pip install -r requirements.txt
```

Ожидаемый результат: установка проходит без ошибок.

---

# 4. Проверка переменных окружения

## 4.1. `.env.example`

- [ ] **BLOCKER** Есть `TELEGRAM_BOT_TOKEN`.
- [ ] **BLOCKER** Есть `TELEGRAM_ADMIN_ID`.
- [ ] **BLOCKER** Есть `TELEGRAM_CHANNEL_ID`.
- [ ] **BLOCKER** Есть `TEST_CHANNEL_ID`.
- [ ] **BLOCKER** Есть `OPENAI_API_KEY`.
- [ ] **BLOCKER** Есть `OPENAI_MODEL`.
- [ ] **BLOCKER** Есть `OPENAI_TEMPERATURE`.
- [ ] **MAJOR** Есть `PEXELS_API_KEY`.
- [ ] **MAJOR** Есть `UNSPLASH_ACCESS_KEY`.
- [ ] **MAJOR** Есть `PIXABAY_API_KEY`.
- [ ] **MAJOR** Есть `TRAVELPAYOUTS_API_TOKEN`.
- [ ] **MAJOR** Есть `TRAVELPAYOUTS_MARKER`.
- [ ] **BLOCKER** Есть `SCHEDULE_TIMEZONE`.
- [ ] **BLOCKER** Есть `ALLOW_FALLBACK_AUTOPUBLISH`.

## 4.2. Railway

- [ ] **BLOCKER** Все обязательные переменные заданы в Railway.
- [ ] **BLOCKER** Railway Start Command: `python -m src.telegram_app`.
- [ ] **BLOCKER** В Railway нет партнёрских ссылок, которые должны лежать в `configs/services.json`.
- [ ] **BLOCKER** Railway не использует старый start command.
- [ ] **MAJOR** После деплоя `/version` показывает новую версию.

---

# 5. Проверка конфигов

## 5.1. `configs/sources.json`

- [ ] **BLOCKER** JSON читается.
- [ ] **BLOCKER** У каждого источника есть `key`, `name`, `url`, `type`, `mode`, `role`, `genres`.
- [ ] **BLOCKER** Есть старые основные источники.
- [ ] **BLOCKER** Добавлен `https://t.me/hackmytrip`.
- [ ] **BLOCKER** Добавлен `https://vk.com/tourister`.
- [ ] **BLOCKER** Добавлен `https://dzen.ru/tonkostiru?tab=articles`.
- [ ] **BLOCKER** Добавлен `https://t.me/travelnews24`.
- [ ] **BLOCKER** Добавлен `https://t.me/s/travel_tema`.
- [ ] **BLOCKER** Добавлен `https://ru.wikivoyage.org/wiki/Wikivoyage:Все_маршруты`.
- [ ] **BLOCKER** `ptuxon` помечен как `manual` или `style_reference`, не auto.
- [ ] **MAJOR** У источников указаны таймауты или общий механизм таймаута.
- [ ] **MAJOR** У источников есть приоритеты.

## 5.2. `configs/services.json`

- [ ] **BLOCKER** JSON читается.
- [ ] **BLOCKER** Есть `tourjin_bot`.
- [ ] **BLOCKER** У `tourjin_bot` ссылка `https://t.me/TourJin_bot`.
- [ ] **BLOCKER** Есть flights-сервис.
- [ ] **BLOCKER** Есть hotels-сервис.
- [ ] **BLOCKER** Есть tours-сервис.
- [ ] **BLOCKER** Есть insurance-сервис.
- [ ] **BLOCKER** Есть transfer-сервис.
- [ ] **BLOCKER** Есть car_rental-сервис.
- [ ] **BLOCKER** Есть excursions-сервис.
- [ ] **BLOCKER** Есть universal CTA / channel CTA / save/share CTA или логика генерации таких кнопок.
- [ ] **MAJOR** Все ссылки валидны по формату URL.
- [ ] **MAJOR** У каждого сервиса есть допустимые жанры.

## 5.3. `configs/link_rules.json`

- [ ] **BLOCKER** JSON читается.
- [ ] **BLOCKER** `flight_deal` ведёт на flights, не на чужой Telegram.
- [ ] **BLOCKER** `tour_offer` ведёт на tours.
- [ ] **BLOCKER** `hotel_post` ведёт на hotels.
- [ ] **BLOCKER** `visa_or_residence` не вставляет авиабилеты.
- [ ] **BLOCKER** `inspiration_story` допускает отсутствие реферальной ссылки.
- [ ] **BLOCKER** Если ссылки неуместны, включаются универсальные CTA-кнопки.

## 5.4. `configs/fallback_topics.json`

- [ ] **BLOCKER** Есть минимум 40 fallback-тем.
- [ ] **BLOCKER** Есть категории: бюджет, практические гайды, необычные места, гастротуризм, активный отдых, вдохновение, ТОП-подборки.
- [ ] **BLOCKER** У каждой темы есть `base_topic`, `category`, `possible_angles`, `preferred_genres`.
- [ ] **MAJOR** Есть правило не повторять `base_topic` минимум 14 дней.
- [ ] **MAJOR** Есть правило не повторять `angle` никогда без существенного изменения.

## 5.5. `configs/media_sources.json`

- [ ] **BLOCKER** Есть Pexels.
- [ ] **MAJOR** Есть Unsplash.
- [ ] **MAJOR** Есть Pixabay.
- [ ] **MAJOR** Есть Mixkit / видео-источники, если видео включено.
- [ ] **BLOCKER** У каждого медиа-источника указаны license rules.
- [ ] **BLOCKER** Есть запрет на автоматическое использование картинок из чужих Telegram-каналов.

---

# 6. Проверка промтов

## 6.1. `prompts/system_editor_ru.md`

- [ ] **BLOCKER** Роль: главный редактор travel Telegram-канала.
- [ ] **BLOCKER** Запрещён копипаст.
- [ ] **BLOCKER** Источник описан как сырьё.
- [ ] **BLOCKER** Указан русский язык.
- [ ] **BLOCKER** Запрещены технические слова в публичном посте.
- [ ] **BLOCKER** Есть цель: прочитать, сохранить, переслать, обсудить, открыть кнопку.

## 6.2. `prompts/writer_3_variants_ru.md`

- [ ] **BLOCKER** Требует 3 разных варианта.
- [ ] **BLOCKER** Варианты не должны повторять друг друга.
- [ ] **BLOCKER** Есть разные стили: вдохновляющий, практичный, продающий/вовлекающий.
- [ ] **BLOCKER** Требуется JSON-ответ.
- [ ] **BLOCKER** Есть запрет на шаблонные фразы.
- [ ] **BLOCKER** Есть требование Telegram-оформления.
- [ ] **BLOCKER** Есть требование не писать служебные блоки в публичном посте.

## 6.3. `prompts/quality_selector_ru.md`

- [ ] **BLOCKER** Минимум качества для автопубликации 85.
- [ ] **BLOCKER** Проверяется заголовок.
- [ ] **BLOCKER** Проверяется первый экран.
- [ ] **BLOCKER** Проверяется конкретика.
- [ ] **BLOCKER** Проверяется CTA.
- [ ] **BLOCKER** Проверяется отсутствие AI-smell.
- [ ] **BLOCKER** Проверяется оформление.

---

# 7. Проверка исходного кода по модулям

## 7.1. `src/telegram_app.py`

- [ ] **BLOCKER** Команда `/start` работает.
- [ ] **BLOCKER** Команда `/version` работает.
- [ ] **BLOCKER** Команда `/test` работает.
- [ ] **BLOCKER** Команда `/run_once` работает.
- [ ] **BLOCKER** Команды `/autopost_on` и `/autopost_off` работают.
- [ ] **BLOCKER** Команды `/schedule` и `/schedule_set` работают.
- [ ] **BLOCKER** Команды каналов работают: `/channels`, `/add_channel`, `/remove_channel`, `/set_channels`.
- [ ] **BLOCKER** `/run_once` возвращает админу отчёт.
- [ ] **BLOCKER** Ошибка не проглатывается молча.

## 7.2. `src/source_manager.py`

- [ ] **BLOCKER** Источники обходятся round-robin.
- [ ] **BLOCKER** Не берётся пачка из одного источника подряд.
- [ ] **BLOCKER** Есть таймаут на источник.
- [ ] **BLOCKER** Если источник упал — бот идёт дальше.
- [ ] **BLOCKER** Возвращается список сигналов с source metadata.
- [ ] **MAJOR** Есть поддержка Telegram public HTML.
- [ ] **MAJOR** Есть поддержка сайтов.
- [ ] **MAJOR** Есть поддержка evergreen/Wikivoyage.

## 7.3. `src/source_health.py`

- [ ] **BLOCKER** Записывает статус каждого источника.
- [ ] **BLOCKER** Пишет ошибку, если источник не ответил.
- [ ] **BLOCKER** Пишет количество найденных сигналов.
- [ ] **BLOCKER** Данные видны в `/status` или `/sources`.

## 7.4. `src/fallback_topic_engine.py`

- [ ] **BLOCKER** Включается, если нет рабочих сигналов.
- [ ] **BLOCKER** Выбирает тему из fallback_topics.
- [ ] **BLOCKER** Генерирует уникальный angle.
- [ ] **BLOCKER** Проверяет `fallback_history.json`.
- [ ] **BLOCKER** Не повторяет тот же угол.

## 7.5. `src/topic_guard.py`

- [ ] **BLOCKER** Отсекает IT, крипту, вакансии, вебинары.
- [ ] **BLOCKER** Отсекает политические темы.
- [ ] **BLOCKER** Отсекает чужую рекламу без travel-ценности.
- [ ] **BLOCKER** Не отсекает хорошие travel-сигналы.

## 7.6. `src/topic_classifier.py`

- [ ] **BLOCKER** Определяет жанр.
- [ ] **BLOCKER** Определяет слот.
- [ ] **BLOCKER** Не называет всё `flight_deal`.
- [ ] **BLOCKER** Различает inspiration, practical, offer, top-list, route, news, event.

## 7.7. `src/scoring_engine.py`

- [ ] **BLOCKER** Считает свежесть.
- [ ] **BLOCKER** Считает конкретику.
- [ ] **BLOCKER** Считает актуальность для россиян.
- [ ] **BLOCKER** Считает визуальный потенциал.
- [ ] **BLOCKER** Считает пользу.
- [ ] **BLOCKER** Считает вовлечение.
- [ ] **BLOCKER** Считает соответствие слоту.

## 7.8. `src/rotation_engine.py`

- [ ] **BLOCKER** Не повторяет источник подряд.
- [ ] **BLOCKER** Не повторяет жанр подряд.
- [ ] **BLOCKER** Не повторяет страну/город подряд.
- [ ] **BLOCKER** Учитывает последние публикации.
- [ ] **BLOCKER** Если есть альтернатива, выбирает альтернативу.

## 7.9. `src/dedup_engine.py`

- [ ] **BLOCKER** Проверяет URL.
- [ ] **BLOCKER** Проверяет заголовок.
- [ ] **BLOCKER** Проверяет смысловой hash.
- [ ] **BLOCKER** Проверяет fallback angle.
- [ ] **MAJOR** Проверяет похожесть на последние публикации.

## 7.10. `src/ai_writer.py`

- [ ] **BLOCKER** Отправляет brief в OpenAI.
- [ ] **BLOCKER** Получает 3 варианта.
- [ ] **BLOCKER** Нормализует кривой JSON.
- [ ] **BLOCKER** Если GPT вернул строку вместо списка, код не падает.
- [ ] **BLOCKER** Если GPT вернул невалидные кнопки, код не падает.
- [ ] **BLOCKER** Если GPT вернул плохие варианты, запускается регенерация или отчёт.

## 7.11. `src/engagement_engine.py`

- [ ] **BLOCKER** Добавляет вовлечение по жанру.
- [ ] **BLOCKER** Не вставляет одинаковый CTA в каждый пост.
- [ ] **BLOCKER** Умеет предложить сохранить, переслать, обсудить, выбрать.

## 7.12. `src/cta_engine.py`

- [ ] **BLOCKER** Читает `services.json`.
- [ ] **BLOCKER** Читает `link_rules.json`.
- [ ] **BLOCKER** Не вставляет реферальные ссылки не по смыслу.
- [ ] **BLOCKER** Если нет подходящей ссылки — ставит универсальные кнопки.
- [ ] **BLOCKER** Flight deal ведёт на flights.
- [ ] **BLOCKER** Visa/payment не ведёт на flights.
- [ ] **BLOCKER** TourJin используется уместно, не в каждом посте.

## 7.13. `src/media_engine.py` и `src/media_sources.py`

- [ ] **BLOCKER** Ищет фото на русском.
- [ ] **BLOCKER** Ищет фото на английском.
- [ ] **BLOCKER** Расширяет запрос.
- [ ] **BLOCKER** Не берёт чужие Telegram-картинки.
- [ ] **BLOCKER** Если фото нет — вызывает генерацию изображения или универсальный fallback.
- [ ] **BLOCKER** Не публикует белую карточку вместо фото.
- [ ] **MAJOR** Хранит источник и лицензию медиа.

## 7.14. `src/image_generation.py`

- [ ] **BLOCKER** Генерирует картинку, если фото не найдено.
- [ ] **BLOCKER** Генерирует без текста на изображении, если нет гарантии качества текста.
- [ ] **BLOCKER** Не генерирует чужие логотипы.
- [ ] **BLOCKER** Не генерирует политические/спорные изображения.

## 7.15. `src/telegram_post_writer.py`

- [ ] **BLOCKER** Форматирует заголовок жирным.
- [ ] **BLOCKER** Не публикует служебные слова `CTA`, `визуал`, `лид`.
- [ ] **BLOCKER** Добавляет пустые строки.
- [ ] **BLOCKER** Следит за хештегами в конце.
- [ ] **BLOCKER** Проверяет длину caption.
- [ ] **BLOCKER** Если caption слишком длинный, делит на 2 части.
- [ ] **BLOCKER** В конце первой части пишет `Продолжение следует 👇`.
- [ ] **BLOCKER** Вторая часть публикуется следом.
- [ ] **BLOCKER** Хештеги уходят во вторую часть, если пост разделён.

## 7.16. `src/publisher.py`

- [ ] **BLOCKER** Публикует в основной канал.
- [ ] **BLOCKER** Публикует в тестовый канал при тесте.
- [ ] **BLOCKER** Поддерживает несколько каналов.
- [ ] **BLOCKER** Делает retry при Telegram timeout.
- [ ] **BLOCKER** Если фото не отправилось, использует fallback.
- [ ] **BLOCKER** Если кнопка невалидна, убирает её и публикует.
- [ ] **BLOCKER** Возвращает результат публикации по каждому каналу.

## 7.17. `src/scheduler.py`

- [ ] **BLOCKER** Запускается внутри event loop Telegram-приложения.
- [ ] **BLOCKER** Не вызывает `RuntimeError: no running event loop`.
- [ ] **BLOCKER** Использует `SCHEDULE_TIMEZONE`.
- [ ] **BLOCKER** Показывает следующий запуск.
- [ ] **BLOCKER** Не запускает две публикации одновременно.
- [ ] **BLOCKER** При сбое уведомляет админа.

## 7.18. `src/diagnostics.py`

- [ ] **BLOCKER** Создаёт run_id.
- [ ] **BLOCKER** Записывает старт запуска.
- [ ] **BLOCKER** Записывает результат каждого этапа.
- [ ] **BLOCKER** Формирует отчёт для админа.
- [ ] **BLOCKER** Видно, где именно сорвался pipeline.

---

# 8. Проверка последовательности pipeline

Для `/run_once` выполнить dry-run с логами.

Ожидаемая последовательность:

- [ ] **BLOCKER** diagnostics.start_run() вызван первым.
- [ ] **BLOCKER** source_manager.collect() проверил источники.
- [ ] **BLOCKER** source_health.update() записал статусы.
- [ ] **BLOCKER** Если сигналов нет, fallback_topic_engine.generate() вызван.
- [ ] **BLOCKER** topic_guard отфильтровал мусор.
- [ ] **BLOCKER** signal_extractor обогатил данные.
- [ ] **BLOCKER** topic_classifier определил жанр.
- [ ] **BLOCKER** scoring_engine поставил score.
- [ ] **BLOCKER** dedup_engine убрал повторы.
- [ ] **BLOCKER** rotation_engine выбрал лучшего кандидата.
- [ ] **BLOCKER** editorial_brief_engine создал brief.
- [ ] **BLOCKER** ai_writer создал 3 варианта.
- [ ] **BLOCKER** quality_selector выбрал лучший.
- [ ] **BLOCKER** cta_engine подобрал кнопки.
- [ ] **BLOCKER** media_engine нашёл или сгенерировал медиа.
- [ ] **BLOCKER** telegram_post_writer проверил длину и формат.
- [ ] **BLOCKER** publisher опубликовал.
- [ ] **BLOCKER** state_store сохранил результат.
- [ ] **BLOCKER** diagnostics.finish_run() отправил отчёт.

---

# 9. Проверка ручного режима

Команды:

```text
/test
/test 1
/test 2
/test 3
```

Ожидаемый результат:

- [ ] **BLOCKER** Каждый тест даёт тему.
- [ ] **BLOCKER** `/test 1`, `/test 2`, `/test 3` не показывают один и тот же источник подряд, если есть альтернатива.
- [ ] **BLOCKER** Каждый тест показывает 3 варианта.
- [ ] **BLOCKER** Есть кнопки публикации вариантов.
- [ ] **BLOCKER** Есть кнопка переписать.
- [ ] **BLOCKER** Есть кнопка отклонить.
- [ ] **BLOCKER** Варианты реально разные.
- [ ] **BLOCKER** Варианты не содержат служебных слов.
- [ ] **BLOCKER** Варианты оформлены как Telegram-посты.

---

# 10. Проверка автопостинга

Команды:

```text
/autopost_on
/status
/run_once
```

Ожидаемый результат:

- [ ] **BLOCKER** `/autopost_on` включает автопостинг.
- [ ] **BLOCKER** `/status` показывает, что автопостинг включён.
- [ ] **BLOCKER** `/status` показывает расписание.
- [ ] **BLOCKER** `/status` показывает следующий запуск.
- [ ] **BLOCKER** `/run_once` публикует пост или даёт полный отчёт причины.
- [ ] **BLOCKER** Плановый запуск публикует пост или даёт отчёт причины.
- [ ] **BLOCKER** При задержке Telegram есть retry.
- [ ] **BLOCKER** При ошибке публикации админу приходит сообщение.

---

# 11. Проверка fallback-сценария

Искусственно отключить источники или подменить список источников нерабочими URL.

Ожидаемый результат:

- [ ] **BLOCKER** Бот не зависает.
- [ ] **BLOCKER** Бот пишет, что источники недоступны.
- [ ] **BLOCKER** Бот выбирает fallback-тему.
- [ ] **BLOCKER** Бот генерирует уникальный angle.
- [ ] **BLOCKER** Бот публикует fallback-пост.
- [ ] **BLOCKER** Fallback-пост не выглядит как аварийная заглушка.
- [ ] **BLOCKER** Fallback-пост проходит качество 85+.

---

# 12. Проверка реферальных ссылок и универсальных кнопок

## 12.1. Офферный пост

- [ ] **BLOCKER** Есть кнопка flights/tours/hotels по смыслу.
- [ ] **BLOCKER** Кнопка не ведёт на чужой Telegram.
- [ ] **BLOCKER** Текст кнопки соответствует обещанию.

## 12.2. Вдохновляющий пост

- [ ] **BLOCKER** Нет грубой продажи.
- [ ] **BLOCKER** Если реферальная ссылка неуместна, стоят универсальные кнопки.
- [ ] **BLOCKER** Можно сохранить/отправить другу/подписаться.

## 12.3. Виза/карты

- [ ] **BLOCKER** Нет авиабилетов, если тема не про поездку.
- [ ] **BLOCKER** CTA мягкий.
- [ ] **BLOCKER** Есть foreign_cards/insurance только если уместно.

---

# 13. Проверка медиа

## 13.1. Поиск фото

- [ ] **BLOCKER** Поиск сначала RU query.
- [ ] **BLOCKER** Потом EN query.
- [ ] **BLOCKER** Потом расширенный query.
- [ ] **BLOCKER** Потом location-based query.
- [ ] **BLOCKER** Если фото нет — генерация изображения.
- [ ] **BLOCKER** Если генерация не работает — универсальный travel fallback.

## 13.2. Релевантность

- [ ] **BLOCKER** Пост про город — фото города.
- [ ] **BLOCKER** Пост про море — море/курорт.
- [ ] **BLOCKER** Пост про еду — релевантная еда.
- [ ] **BLOCKER** Пост про flight_deal — фото города назначения или нормальный fallback, не белая карточка.

## 13.3. Публикация медиа

- [ ] **BLOCKER** Если фото не отправилось, бот не падает.
- [ ] **BLOCKER** Если caption длинный, пост делится на 2 части.
- [ ] **BLOCKER** Первая часть с фото заканчивается `Продолжение следует 👇`.
- [ ] **BLOCKER** Вторая часть публикуется следом.

---

# 14. Проверка оформления поста

- [ ] **BLOCKER** Есть заголовок.
- [ ] **BLOCKER** Заголовок жирный.
- [ ] **BLOCKER** Есть лид.
- [ ] **BLOCKER** Нет стены текста.
- [ ] **BLOCKER** Есть пустые строки между блоками.
- [ ] **BLOCKER** Разделители не используются чрезмерно.
- [ ] **BLOCKER** Эмодзи умеренно.
- [ ] **BLOCKER** Хештеги в конце.
- [ ] **BLOCKER** Нет служебных слов `CTA`, `визуал`, `лид`, `подзаголовок`.
- [ ] **BLOCKER** Markdown/HTML корректно рендерится в Telegram.
- [ ] **BLOCKER** Пост выглядит как публикация канала, а не как черновик ТЗ.

---

# 15. Проверка качества текста

- [ ] **BLOCKER** Заголовок цепляет.
- [ ] **BLOCKER** Первый экран объясняет, зачем читать дальше.
- [ ] **BLOCKER** Есть конкретика.
- [ ] **BLOCKER** Нет школьного пересказа.
- [ ] **BLOCKER** Нет пресс-релиза.
- [ ] **BLOCKER** Нет запрещённых фраз.
- [ ] **BLOCKER** Нет англицизмов без смысла.
- [ ] **BLOCKER** Концовка логична.
- [ ] **BLOCKER** CTA соответствует жанру.
- [ ] **BLOCKER** Пост хочется сохранить/переслать/обсудить/открыть.

---

# 16. Проверка публикации в Telegram

- [ ] **BLOCKER** Бот является администратором канала.
- [ ] **BLOCKER** У бота есть право публиковать.
- [ ] **BLOCKER** Указан правильный `TELEGRAM_CHANNEL_ID`.
- [ ] **BLOCKER** Указан правильный `TEST_CHANNEL_ID`.
- [ ] **BLOCKER** Тестовая публикация выходит в тестовый канал.
- [ ] **BLOCKER** Боевая публикация выходит в основной канал.
- [ ] **BLOCKER** Кнопки отображаются.
- [ ] **BLOCKER** Форматирование отображается.
- [ ] **BLOCKER** Если Telegram задерживает отправку, бот делает retry.
- [ ] **BLOCKER** Результат публикации записан в state/log.

---

# 17. Проверка расписания

- [ ] **BLOCKER** `/schedule` показывает расписание.
- [ ] **BLOCKER** `/schedule_set 09:00,14:00,19:00` меняет расписание.
- [ ] **BLOCKER** `/status` показывает timezone.
- [ ] **BLOCKER** `/status` показывает следующий запуск.
- [ ] **BLOCKER** Плановый запуск реально стартует.
- [ ] **BLOCKER** При плановом запуске не создаются дубли.
- [ ] **BLOCKER** Если запуск уже идёт, второй не стартует.

---

# 18. Проверка каналов

- [ ] **BLOCKER** `/channels` показывает список каналов.
- [ ] **BLOCKER** `/add_channel` добавляет канал.
- [ ] **BLOCKER** `/remove_channel` удаляет канал.
- [ ] **BLOCKER** `/set_channels` заменяет список каналов.
- [ ] **BLOCKER** Публикация идёт во все активные каналы.
- [ ] **BLOCKER** Если один канал недоступен, остальные не блокируются.
- [ ] **MAJOR** По каждому каналу есть результат публикации.

---

# 19. Проверка хранения состояния

- [ ] **BLOCKER** `data/state.json` создаётся и читается.
- [ ] **BLOCKER** `publication_log.json` обновляется.
- [ ] **BLOCKER** `rejected_topics.json` обновляется.
- [ ] **BLOCKER** `source_health.json` обновляется.
- [ ] **BLOCKER** `fallback_history.json` обновляется.
- [ ] **BLOCKER** После перезапуска Railway бот помнит историю.
- [ ] **BLOCKER** После перезапуска не публикует тот же пост повторно.

---

# 20. Проверка устойчивости к ошибкам

Искусственно проверить:

- [ ] **BLOCKER** OpenAI возвращает кривой JSON — бот не падает.
- [ ] **BLOCKER** OpenAI timeout — бот делает retry или пишет отчёт.
- [ ] **BLOCKER** Источник timeout — бот идёт дальше.
- [ ] **BLOCKER** Все источники timeout — fallback.
- [ ] **BLOCKER** Pexels timeout — Unsplash/Pixabay/generation/fallback.
- [ ] **BLOCKER** Telegram timeout — retry.
- [ ] **BLOCKER** Невалидная кнопка — убрать кнопку и публиковать.
- [ ] **BLOCKER** Слишком длинный caption — split на 2 части.
- [ ] **BLOCKER** Ошибка одного канала не ломает публикацию в другие.

---

# 21. Минимальный набор тестов перед деплоем

Команды локально:

```bash
python -m compileall -q src tests
python tests/validate_project.py
python tests/test_rotation.py
python tests/test_cta_rules.py
python tests/test_media_policy.py
python tests/test_publish_split.py
python tests/test_pipeline_dryrun.py
```

Ожидаемый результат: все тесты проходят.

---

# 22. Минимальный набор Telegram-проверок после деплоя

В боте выполнить:

```text
/version
/status
/sources
/services
/test 1
/test 2
/test 3
/run_once
```

Ожидаемый результат:

- [ ] **BLOCKER** `/version` показывает актуальную версию.
- [ ] **BLOCKER** `/status` показывает состояние.
- [ ] **BLOCKER** `/sources` показывает source health.
- [ ] **BLOCKER** `/services` показывает сервисы.
- [ ] **BLOCKER** `/test 1-3` дают разные темы.
- [ ] **BLOCKER** `/run_once` публикует или даёт полный отчёт.

---

# 23. Финальная приёмка

Проект можно считать готовым только если:

- [ ] **BLOCKER** Бот публикует пост через `/run_once`.
- [ ] **BLOCKER** Бот публикует пост по расписанию.
- [ ] **BLOCKER** Бот не залипает на одном источнике.
- [ ] **BLOCKER** Бот не повторяет один жанр подряд при наличии альтернативы.
- [ ] **BLOCKER** Бот генерирует fallback-пост, если источники недоступны.
- [ ] **BLOCKER** Бот не молчит при ошибке.
- [ ] **BLOCKER** Бот пишет отчёт админу.
- [ ] **BLOCKER** Посты выглядят как Telegram travel-канал.
- [ ] **BLOCKER** Посты не содержат старых шаблонов.
- [ ] **BLOCKER** CTA и ссылки уместны.
- [ ] **BLOCKER** Если ссылок нет — есть универсальные кнопки.
- [ ] **BLOCKER** Медиа релевантно или сгенерировано.
- [ ] **BLOCKER** Длинный пост с фото делится на 2 части.
- [ ] **BLOCKER** Все ключевые ошибки обработаны.

---

# 24. Главный критерий

Финальный бот должен быть не набором файлов, а рабочей системой:

```text
нашёл повод
→ понял смысл
→ выбрал угол
→ написал хороший пост
→ оформил красиво
→ поставил уместные кнопки
→ подобрал или сгенерировал медиа
→ опубликовал
→ объяснил результат
→ запомнил историю
```

Если хотя бы один этап не работает или молчит, комплект нельзя считать финальным.
