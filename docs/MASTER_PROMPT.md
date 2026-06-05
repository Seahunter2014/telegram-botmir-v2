# РАСШИРЕННОЕ ТЗ / MASTER PROMPT

## На разработку Telegram-бота AI-редактора для travel-канала «Мир на ладони»

---

# 0. Главная установка

Нужно разработать не шаблонный генератор постов, а полноценного Telegram-бота в формате AI-редакции travel-канала.

Бот должен работать как редакция:

* сам ищет свежие темы;
* сам определяет жанр;
* сам понимает, какой пост нужен: вдохновляющий, полезный, продающий, событийный, новостной, вовлекающий;
* сам пишет авторский Telegram-пост;
* не копирует источник;
* не делает тупой пересказ;
* не использует старые шаблоны;
* не пишет «нейросетевую воду»;
* не повторяет одинаковые структуры;
* не публикует похожие темы подряд;
* не делает рерайт старого поста как новый;
* сам вставляет реферальные ссылки только там, где они уместны;
* в ручном режиме показывает 3 варианта на выбор;
* в автопостинге сам выбирает лучший вариант и публикует без ручного выбора.

Весь интерфейс, промты, комментарии, документация, логика и описания должны быть на русском языке. Английский допустим только в названиях файлов, переменных окружения, классов, функций, API и официальных названиях сервисов.

---

# 1. Что именно должен делать бот

Бот должен:

1. Обходить список источников по кругу.
2. Получать свежие сигналы: новости, офферы, идеи поездок, события, туры, перелёты, статьи, визовые и релокационные поводы.
3. Проверять свежесть сигнала.
4. Проверять, не была ли похожая тема уже опубликована.
5. Проверять, не повторяется ли жанр, страна, город, источник или структура поста слишком часто.
6. Классифицировать сигнал в один или несколько жанров.
7. Оценивать тему по скорингу.
8. Выбирать лучшую тему под текущий слот публикации.
9. Делать редакционный план поста.
10. Генерировать 3 разных варианта поста.
11. Проверять каждый вариант на шаблонность, повторы, ошибки, «запах ИИ», внутренние технические фразы и слабую конкретику.
12. Выбирать CTA и реферальные ссылки по жанру.
13. Подбирать медиа.
14. В ручном режиме показывать админу 3 варианта с кнопками.
15. В автопостинге самому выбирать лучший вариант.
16. Публиковать в Telegram-канал.
17. Сохранять историю публикаций.
18. Запоминать, какие темы, жанры, страны, источники и структуры уже были.
19. Не повторять одинаковые посты даже после рерайта.
20. Давать отчёт по последней публикации, последнему пропуску и причине выбора темы.

---

# 2. Чего бот делать НЕ должен

Бот не должен:

* использовать старые шаблоны старого бота;
* хранить старые snapshots с готовыми текстами;
* использовать старый `draft_writer`, если он содержит шаблонные заготовки;
* писать фразы «Есть направления, которые…»;
* писать фразы «Иногда лучшие поездки…»;
* писать «Сигнал для weekend_trip…» или любые внутренние технические фразы;
* копировать источник;
* делать сухой пересказ новости;
* вставлять ссылки ради галочки;
* делать каждый пост продающим;
* публиковать одинаковые или похожие посты;
* публиковать старый инфоповод;
* писать на английском без необходимости;
* использовать англицизмы без смысла: «вайб», «must visit», «релакс», «чилл», «топчик», «Pinterest», «wow-эффект»;
* отправлять длинный пост caption к фото, если текст может обрезаться;
* публиковать текст с битой кодировкой;
* публиковать пост, в котором нет логической концовки;
* публиковать пост без конкретики, если тема требует конкретики;
* публиковать рекламный текст там, где нужен вдохновляющий или вовлекающий пост.

---

# 3. Режимы работы

## 3.1. Ручной режим

Команды:

* `/test`
* `/preview`
* `/rewrite`
* `/softer`
* `/sales`
* `/reject`
* `/publish`

В ручном режиме бот:

1. Находит тему.
2. Делает редакционный план.
3. Генерирует 3 варианта поста:

   * вариант 1 — более вдохновляющий;
   * вариант 2 — более практичный;
   * вариант 3 — более продающий, вирусный или эмоциональный в зависимости от жанра.
4. Показывает админу:

   * источник;
   * жанр;
   * score темы;
   * почему тема выбрана;
   * 3 варианта текста;
   * предлагаемые кнопки/ссылки;
   * предупреждения фактчека.
5. Даёт inline-кнопки:

   * «Опубликовать вариант 1»
   * «Опубликовать вариант 2»
   * «Опубликовать вариант 3»
   * «Переписать»
   * «Сделать мягче»
   * «Сделать продающе»
   * «Отклонить тему»

## 3.2. Автопостинг

В автопостинге человек ничего не выбирает.

Бот:

1. Сам выбирает тему.
2. Сам генерирует 3 варианта внутри себя.
3. Сам оценивает варианты по качеству.
4. Сам выбирает лучший.
5. Сам проверяет дубли и шаблонность.
6. Сам публикует.
7. Сам сохраняет публикацию в историю.

---

# 4. Расписание и логика слотов

Базовые слоты:

* 09:00 — вдохновение, красивые направления, необычные места, мягкий travel-интерес;
* 14:00 — офферы, перелёты, туры, отели, конкретные локации, коммерческие поводы;
* 19:00 — полезное, визы, правила, лайфхаки, события, активности, практический travel.

Это не жёсткая тюрьма. Если в нужном слоте нет сильной темы, бот берёт другую лучшую тему, но обязан не повторять похожую тему, жанр, страну, город, источник и структуру подряд.

## Утренний слот

Предпочтительные жанры:

* `destination_post`
* `hidden_places`
* `city_break`
* `weekend_trip`
* `beach_trip`
* `mountain_trip`
* `gastronomy_trip`
* `romantic_trip`
* `luxury_escape`
* `viral_travel`
* `inspiration_story`

Цель: вызвать желание сохранить, переслать, поставить реакцию, подумать о поездке.

## Дневной слот

Предпочтительные жанры:

* `flight_deal`
* `tour_offer`
* `hotel_post`
* `premium_hotel`
* `last_minute`
* `family_trip`
* `event_trip`
* `weekend_activity`

Цель: дать конкретное предложение или повод к действию.

## Вечерний слот

Предпочтительные жанры:

* `practical_travel`
* `travel_hack`
* `visa_or_residence`
* `relocation`
* `payment_abroad`
* `airport_lounge`
* `insurance_tip`
* `concert_trip`
* `discussion_post`

Цель: польза, сохранение, обсуждение, вовлечение.

---

# 5. Полный каталог тем

## 5.1. Направления и вдохновение

### `destination_post`

Пост о стране, городе, регионе, острове, маршруте или месте.

Используется, когда источник даёт повод рассказать о направлении.

Цель:

* вдохновить;
* объяснить, почему туда стоит смотреть сейчас;
* дать практический смысл поездки;
* мягко подвести к билетам, отелям или экскурсиям.

Ссылки:

* flights;
* hotels;
* tours.

Максимум ссылок: 2.

---

### `weekend_trip`

Короткая поездка на 2–3 дня.

Цель:

* показать, что поездку можно собрать без длинного отпуска;
* дать ощущение лёгкости;
* предложить город, море, событие или активность.

Ссылки:

* flights;
* hotels;
* tours.

Максимум ссылок: 2.

---

### `city_break`

Городская поездка на 2–4 дня.

Примеры городов:

* Стамбул;
* Ереван;
* Тбилиси;
* Баку;
* Белград;
* Дубай;
* Рим;
* Париж;
* Барселона;
* Прага.

Ссылки:

* flights;
* hotels;
* excursions.

---

### `beach_trip`

Пляжный отдых, море, острова, курорты.

Ссылки:

* tours;
* hotels;
* flights;
* insurance;
* transfer.

---

### `mountain_trip`

Горы, природа, озёра, каньоны, перезагрузка.

Ссылки:

* hotels;
* excursions;
* car_rental;
* transfer;
* insurance.

---

### `gastronomy_trip`

Путешествие ради еды, вина, рынков, ресторанов, гастрономии.

Ссылки:

* flights;
* hotels;
* excursions.

---

### `romantic_trip`

Поездка для пары.

Ссылки:

* hotels;
* flights;
* tours;
* excursions.

---

### `family_trip`

Семейный отдых.

Ссылки:

* tours;
* hotels;
* insurance.

Максимум ссылок: 2.

---

### `luxury_escape`

Премиальный отдых, красивые отели, острова, виллы, luxury-направления.

Ссылки:

* hotels;
* tours;
* transfer;
* индивидуальный подбор.

---

### `hidden_places`

Неочевидные места.

Ссылки:

* excursions;
* hotels;
* flights.

---

### `inspiration_story`

Непродающий вдохновляющий пост.

Ссылки:

* нет.

Цель:

* реакции;
* пересылки;
* сохранения;
* эмоциональная привязка к каналу.

---

## 5.2. Коммерческие темы

### `flight_deal`

Перелёт, дешёвый билет, акция, интересный маршрут.

Ссылки:

* flights;
* hotels.

Максимум ссылок: 2.

---

### `tour_offer`

Тур, готовая поездка, пакетное предложение.

Ссылки:

* tours;
* insurance.

Максимум ссылок: 2.

---

### `hotel_post`

Пост об отеле или проживании.

Ссылки:

* hotels;
* tours.

Максимум ссылок: 2.

---

### `premium_hotel`

Красивый, необычный или премиальный отель.

Ссылки:

* hotels;
* transfer;
* flights.

---

### `last_minute`

Горящее предложение.

Ссылки:

* tours;
* flights;
* hotels.

---

### `hot_tour`

Горящий тур.

Ссылки:

* Travelata hot tours;
* insurance.

---

### `seasonal_offer`

Сезонное предложение.

Ссылки:

* tours;
* hotels;
* flights.

---

## 5.3. Практические темы

### `practical_travel`

Полезный travel-пост.

Ссылки:

* foreign_cards;
* insurance.

Максимум ссылок: 1.

---

### `travel_hack`

Лайфхак.

Ссылки:

* сервис по смыслу;
* максимум 1.

---

### `visa_or_residence`

Визы, ВНЖ, правила въезда, документы.

Ссылки:

* foreign_cards;
* insurance.

Максимум ссылок: 1.

Формат CTA: мягкий.

---

### `relocation`

Релокация, жизнь за границей, долгий stay.

Ссылки:

* foreign_cards;
* insurance.

---

### `payment_abroad`

Оплата за границей, зарубежные карты, SWIFT, карты для путешествий.

Ссылки:

* foreign_cards.

Максимум ссылок: 2.

---

### `airport_lounge`

Лаунжи, аэропорты, пересадки, комфорт.

Ссылки:

* airport;
* flights.

---

### `insurance_tip`

Страховка, медицина, безопасность.

Ссылки:

* insurance.

---

## 5.4. События и активности

### `event_trip`

Событие как повод для поездки.

Ссылки:

* events;
* flights;
* hotels.

Максимум ссылок: 3.

---

### `concert_trip`

Концерт мирового артиста как повод для поездки.

Ссылки:

* events;
* flights;
* hotels.

---

### `sports_trip`

Спортивное событие.

Ссылки:

* events;
* flights;
* hotels.

---

### `weekend_activity`

Активность на выходные.

Ссылки:

* excursions;
* flights;
* hotels.

Максимум ссылок: 3.

---

### `activities_post`

Парк, музей, аквапарк, аттракцион, активность, развлечение.

Ссылки:

* excursions;
* flights;
* hotels.

Максимум ссылок: 3.

---

### `excursion_post`

Экскурсии, прогулки, гиды, маршруты.

Ссылки:

* excursions.

---

## 5.5. Транспорт и маршруты

### `rail_trip`

Поезда, железные дороги, маршруты.

Ссылки:

* ground_transport;
* rail_europe;
* trip_rail.

---

### `bus_trip`

Автобусы, наземные переезды.

Ссылки:

* ground_transport.

---

### `road_trip`

Маршрут на машине.

Ссылки:

* car_rental;
* hotels;
* excursions.

---

### `airport_transfer`

Трансфер из аэропорта.

Ссылки:

* transfer.

---

## 5.6. Вовлекающие и вирусные темы

### `viral_travel`

Пост, который хочется переслать.

Ссылки:

* обычно нет.

---

### `discussion_post`

Пост для обсуждения.

Ссылки:

* нет.

---

### `unusual_hotel`

Необычный отель.

Ссылки:

* hotels.

---

### `weird_travel`

Странное, необычное, удивительное в путешествиях.

Ссылки:

* по ситуации.

---

# 6. Полный реестр источников

Источники должны лежать в `configs/sources.json`.

## 6.1. Vandrouki

Ключ: `vandrouki`
Название: Vandrouki
Тип: telegram
Роль: offers
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: telegram_public_html
Ссылка: [https://t.me/s/vandroukiru](https://t.me/s/vandroukiru)

Использовать для:

* `flight_deal`
* `weekend_trip`
* `last_minute`
* `destination_post`

Правило:
брать только суть: направление, цена, даты, город вылета, условия. Текст не копировать.

---

## 6.2. Aviasales Telegram

Ключ: `aviasales_telegram`
Название: Авиасейлс Telegram
Тип: telegram
Роль: style_and_flights
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: telegram_public_html
Ссылка: [https://t.me/s/aviasales](https://t.me/s/aviasales)

Использовать для:

* `flight_deal`
* `city_break`
* `weekend_trip`
* `destination_post`

---

## 6.3. Travelata Telegram

Ключ: `travelata_telegram`
Название: Travelata Telegram
Тип: telegram
Роль: tours
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: telegram_public_html
Ссылка: [https://t.me/s/travelata](https://t.me/s/travelata)

Использовать для:

* `tour_offer`
* `hot_tour`
* `seasonal_offer`
* `beach_trip`
* `family_trip`

---

## 6.4. ПСЖР / Авиасейлс

Ключ: `psgr_journal`
Название: ПСЖР / Авиасейлс
Тип: site
Роль: style_and_signals
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: site_listing
Ссылка: [https://www.aviasales.ru/psgr](https://www.aviasales.ru/psgr)

Использовать для:

* `destination_post`
* `flight_deal`
* `weekend_trip`
* `city_break`

---

## 6.5. TravelAsk

Ключ: `travelask`
Название: TravelAsk
Тип: site
Роль: news_and_commercial_signals
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: site_listing
Ссылка: [https://travelask.ru/](https://travelask.ru/)

Использовать для:

* `destination_post`
* `hidden_places`
* `practical_travel`
* `viral_travel`

---

## 6.6. Журнал Tripster

Ключ: `tripster_journal`
Название: Журнал Трипстера
Тип: site
Роль: inspiration_and_structure
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: site_listing
Ссылка: [https://experience.tripster.ru/journal/](https://experience.tripster.ru/journal/)

Использовать для:

* `city_break`
* `excursion_post`
* `hidden_places`
* `gastronomy_trip`
* `destination_post`

---

## 6.7. Журнал Яндекс Путешествий

Ключ: `yandex_travel_journal`
Название: Журнал Яндекс Путешествий
Тип: site
Роль: regions_and_events
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: site_listing
Ссылка: [https://travel.yandex.ru/journal/](https://travel.yandex.ru/journal/)

Использовать для:

* `destination_post`
* `practical_travel`
* `family_trip`
* `weekend_trip`

---

## 6.8. Горбилет

Ключ: `gorbilet_events`
Название: Горбилет
Тип: site
Роль: events
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: single_article
Ссылка: [https://gorbilet.ru/blog/music/kontserty-mirovyh-zvezd-v-2026](https://gorbilet.ru/blog/music/kontserty-mirovyh-zvezd-v-2026)

Использовать для:

* `event_trip`
* `concert_trip`
* `weekend_activity`

---

## 6.9. ПСЖР: концерты мировых звёзд

Ключ: `psgr_concerts`
Название: ПСЖР: концерты мировых звёзд
Тип: site
Роль: events_and_routes
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: single_article
Ссылка: [https://www.aviasales.ru/psgr/article/konczerty-mirovyh-zvyozd](https://www.aviasales.ru/psgr/article/konczerty-mirovyh-zvyozd)

Использовать для:

* `concert_trip`
* `event_trip`
* `city_break`

---

## 6.10. IMIGRATA

Ключ: `imigrata`
Название: IMIGRATA
Тип: site
Роль: visa_and_residence
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: site_listing
Ссылка: [https://imigrata.com/ru/](https://imigrata.com/ru/)

Использовать для:

* `visa_or_residence`
* `relocation`
* `digital_nomad`
* `payment_abroad`

---

## 6.11. relocate_easy

Ключ: `relocate_easy`
Название: relocate_easy
Тип: telegram
Роль: relocation_signals
Приоритет: B
Режим: auto
Язык: ru
Метод сбора: telegram_public_html
Ссылка: [https://t.me/s/relocate_easy](https://t.me/s/relocate_easy)

Использовать для:

* `relocation`
* `visa_or_residence`

---

## 6.12. ekspat_info

Ключ: `ekspat_info`
Название: ekspat_info
Тип: telegram
Роль: relocation_signals
Приоритет: B
Режим: auto
Язык: ru
Метод сбора: telegram_public_html
Ссылка: [https://t.me/s/ekspat_info](https://t.me/s/ekspat_info)

Использовать для:

* `relocation`
* `digital_nomad`
* `payment_abroad`

---

## 6.13. puteshe

Ключ: `puteshe`
Название: puteshe
Тип: telegram
Роль: beauty_and_inspiration
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: telegram_public_html
Ссылка: [https://t.me/s/puteshe](https://t.me/s/puteshe)

Использовать для:

* `destination_post`
* `hidden_places`
* `weekend_trip`
* `inspiration_story`

---

## 6.14. ptuxon

Ключ: `ptuxon`
Название: ptuxon
Тип: youtube
Роль: style_reference
Приоритет: B
Режим: manual
Язык: ru
Метод сбора: manual_reference
Ссылка: [http://youtube.com/c/ptuxon](http://youtube.com/c/ptuxon)

Использовать только как стилевой референс, не как автоматический источник.

---

## 6.15. Trip.com Activities

Ключ: `trip_activities`
Название: Trip.com Activities
Тип: site
Роль: activities
Приоритет: A
Режим: auto
Язык: ru
Метод сбора: single_article
Ссылка: [https://www.trip.com/t/g39kF7nZrU2](https://www.trip.com/t/g39kF7nZrU2)

Использовать для:

* `activities_post`
* `weekend_activity`
* `event_trip`

---

# 7. Полный реестр сервисов и реферальных ссылок

Ссылки должны храниться в `configs/services.json`, а не в Railway.
В Railway хранятся только секреты и API-ключи.

## 7.1. Ostrovok

Ключ: `ostrovok`
Название: Ostrovok
Категория: hotels
Платформа: Travelpayouts
Ссылка: [https://ostrovok.tp.st/yHBoZUg7](https://ostrovok.tp.st/yHBoZUg7)
Приоритет: 10
Статус: active

Использовать для:

* `hotel_post`
* `destination_post`
* `family_trip`
* `luxury_hotel`
* `premium_hotel`
* `weekend_trip`
* `event_trip`

Текст кнопки:

* «Забронировать отель»
* «Посмотреть отели»
* «Подобрать проживание»

---

## 7.2. Yandex Travel

Ключ: `yandex_travel`
Название: Yandex Travel
Категория: general_travel
Платформа: Travelpayouts
Ссылка: [https://yandex.tp.st/y94GSOah](https://yandex.tp.st/y94GSOah)
Приоритет: 3
Статус: active

Использовать для:

* `destination_post`
* `weekend_trip`
* `family_trip`
* `general_selection`

Текст кнопки:

* «Подобрать поездку»

---

## 7.3. Aviasales

Ключ: `aviasales`
Название: Aviasales
Категория: flights
Платформа: Travelpayouts
Ссылка: [https://aviasales.tp.st/hYipm2Ac](https://aviasales.tp.st/hYipm2Ac)
Приоритет: 10
Статус: active

Использовать для:

* `flight_deal`
* `destination_post`
* `event_trip`
* `weekend_trip`
* `city_break`

Текст кнопки:

* «Найти билеты»
* «Посмотреть перелёты»
* «Билеты в город»

Дополнительная кампания:

* ключ: `special_low_price_map`
* название: «Карта низких цен»
* ссылка: [https://aviasales.tp.st/05TrktsG?erid=2VtzqwmJxgb](https://aviasales.tp.st/05TrktsG?erid=2VtzqwmJxgb)

---

## 7.4. VIP Zal

Ключ: `vip_zal`
Название: VIP Zal
Категория: airport
Платформа: Travelpayouts
Ссылка: [https://vip-zal.tp.st/VUTiM7FJ](https://vip-zal.tp.st/VUTiM7FJ)
Приоритет: 6
Статус: active

Использовать для:

* `flight_deal`
* `business_trip`
* `airport_comfort`
* `airport_lounge`

Текст кнопки:

* «Лаунж в аэропорту»

---

## 7.5. Onlinetours

Ключ: `onlinetours`
Название: Onlinetours
Категория: tours
Платформа: Travelpayouts
Ссылка: [https://onlinetours.tp.st/Um2ycow9](https://onlinetours.tp.st/Um2ycow9)
Приоритет: 9
Статус: active

Использовать для:

* `tour_offer`
* `family_trip`
* `hotel_post`
* `all_inclusive`

Текст кнопки:

* «Лучшие туры»

---

## 7.6. Travelata

Ключ: `travelata`
Название: Travelata
Категория: tours
Платформа: Travelpayouts
Ссылка: [https://travelata.tp.st/O6m2Lg6H](https://travelata.tp.st/O6m2Lg6H)
Приоритет: 9
Статус: active

Использовать для:

* `tour_offer`
* `hot_tour`
* `seasonal_offer`
* `beach_trip`
* `family_trip`

Текст кнопки:

* «Сравнить туры»
* «Посмотреть туры»

Дополнительная кампания:

* ключ: `special_hot_tours`
* название: «Горящие туры»
* ссылка: [https://travelata.tp.st/42HvBmFJ?erid=2VtzqwyVPEu](https://travelata.tp.st/42HvBmFJ?erid=2VtzqwyVPEu)

---

## 7.7. Tutu

Ключ: `tutu`
Название: Tutu
Категория: ground_transport
Платформа: Travelpayouts
Ссылка: [https://tutu.tp.st/dZglLc7q](https://tutu.tp.st/dZglLc7q)
Приоритет: 8
Статус: active

Использовать для:

* `rail_trip`
* `bus_trip`
* `domestic_route`

Текст кнопки:

* «Билеты на транспорт»

---

## 7.8. Rail Europe

Ключ: `rail_europe`
Название: Rail Europe
Категория: rail_europe
Платформа: Travelpayouts
Ссылка: [https://raileurope.tp.st/nWODZ4nI](https://raileurope.tp.st/nWODZ4nI)
Приоритет: 7
Статус: active

Использовать для:

* `europe_route`
* `rail_trip`
* `multi_city_route`

Текст кнопки:

* «Поезда по Европе»

---

## 7.9. Cherehapa

Ключ: `cherehapa`
Название: Cherehapa
Категория: insurance
Платформа: Travelpayouts
Ссылка: [https://cherehapa.tp.st/RIsddc4I](https://cherehapa.tp.st/RIsddc4I)
Приоритет: 10
Статус: active

Использовать для:

* `visa_or_residence`
* `family_trip`
* `long_stay`
* `tour_offer`
* `insurance_tip`
* `practical_travel`

Текст кнопки:

* «Оформить страховку»
* «Проверить страховку»

---

## 7.10. KiwiTaxi

Ключ: `kiwitaxi`
Название: KiwiTaxi
Категория: transfer
Платформа: Travelpayouts
Ссылка: [https://kiwitaxi.tp.st/Ven9kvYz](https://kiwitaxi.tp.st/Ven9kvYz)
Приоритет: 9
Статус: active

Использовать для:

* `airport_transfer`
* `family_trip`
* `late_arrival`
* `beach_trip`
* `premium_hotel`

Текст кнопки:

* «Заказать трансфер»

---

## 7.11. Localrent

Ключ: `localrent`
Название: Localrent
Категория: car_rental
Платформа: Travelpayouts
Ссылка: [https://localrent.tp.st/Q77W1ZWX](https://localrent.tp.st/Q77W1ZWX)
Приоритет: 9
Статус: active

Использовать для:

* `road_trip`
* `destination_post`
* `family_trip`
* `mountain_trip`
* `island_trip`

Текст кнопки:

* «Арендовать авто»

---

## 7.12. BikesBooking

Ключ: `bikesbooking`
Название: BikesBooking
Категория: bike_rental
Платформа: Travelpayouts
Ссылка: [https://bikesbooking.tp.st/eMN1TXvi](https://bikesbooking.tp.st/eMN1TXvi)
Приоритет: 7
Статус: active

Использовать для:

* `beach_destination`
* `island_trip`
* `activity_trip`

Текст кнопки:

* «Прокат байка»

---

## 7.13. Sputnik8

Ключ: `sputnik8`
Название: Sputnik8
Категория: excursions
Платформа: Travelpayouts
Ссылка: [https://sputnik8.tp.st/FQZC0UxF](https://sputnik8.tp.st/FQZC0UxF)
Приоритет: 9
Статус: active

Использовать для:

* `activities_post`
* `destination_post`
* `event_trip`
* `excursion_post`
* `city_break`

Текст кнопки:

* «Найти экскурсии»

---

## 7.14. TicketNetwork

Ключ: `ticketnetwork`
Название: TicketNetwork
Категория: events
Платформа: Travelpayouts
Ссылка: [https://ticketnetwork.tp.st/wCwLXLTc](https://ticketnetwork.tp.st/wCwLXLTc)
Приоритет: 7
Статус: active

Использовать для:

* `event_trip`
* `concert_trip`
* `sports_trip`

Текст кнопки:

* «Билеты на событие»

---

## 7.15. Trip.com Cruises

Ключ: `trip_cruises`
Название: Trip.com
Категория: cruises
Платформа: Direct
Ссылка: [https://www.trip.com/t/LpiQRIoMrU2](https://www.trip.com/t/LpiQRIoMrU2)
Приоритет: 6
Статус: active

Использовать для:

* `cruise_offer`
* `luxury_trip`
* `event_trip`

Текст кнопки:

* «Смотреть круизы»

Дополнительная кампания:

* ключ: `special_hotels_discount`
* название: «Отели со скидкой до 80%»
* ссылка: [https://www.trip.com/t/OdWcYTrlHU2](https://www.trip.com/t/OdWcYTrlHU2)

---

## 7.16. TourJin Bot

Ключ: `tourjin_bot`
Название: TourJin Bot
Категория: general_bot
Платформа: Internal
Ссылка: [https://t.me/TourJin_bot](https://t.me/TourJin_bot)
Приоритет: 2
Статус: active

Использовать для:

* `general_selection`
* `manual_assist`
* `destination_post`

Текст кнопки:

* «Подобрать в TourJin»

---

## 7.17. 5 Карт

Ключ: `five_cards`
Название: 5 Карт
Категория: foreign_cards
Платформа: Direct
Ссылка: [https://5kart.ru/?code=LNGO6MQEX](https://5kart.ru/?code=LNGO6MQEX)
Приоритет: 9
Статус: active

Использовать для:

* `payment_abroad`
* `visa_or_residence`
* `long_stay`
* `digital_nomad`

Текст кнопки:

* «Оформить карту»

---

## 7.18. PPL Travel Visa Platinum

Ключ: `ppl_visa_platinum`
Название: PPL Travel Visa Platinum
Категория: foreign_cards
Платформа: Direct
Ссылка: [https://ppl.travel/product/karta-visa-platinum-s-kreditnym-bin-banka-kirgizii/ref/7503/?utm_campaign=visa-platinum-bin-kg](https://ppl.travel/product/karta-visa-platinum-s-kreditnym-bin-banka-kirgizii/ref/7503/?utm_campaign=visa-platinum-bin-kg)
Приоритет: 8
Статус: active

Использовать для:

* `payment_abroad`
* `visa_or_residence`
* `long_stay`

Текст кнопки:

* «Visa Platinum»

---

## 7.19. PPL Travel Visa Gold

Ключ: `ppl_visa_gold`
Название: PPL Travel Visa Gold
Категория: foreign_cards
Платформа: Direct
Ссылка: [https://ppl.travel/product/karta-visa-gold/ref/7503/?utm_campaign=visa-gold-swift-](https://ppl.travel/product/karta-visa-gold/ref/7503/?utm_campaign=visa-gold-swift-)?
Приоритет: 8
Статус: active

Использовать для:

* `payment_abroad`
* `visa_or_residence`
* `long_stay`

Текст кнопки:

* «Visa Gold»

---

## 7.20. Trip.com Activities

Ключ: `trip_activities`
Название: Trip.com Activities
Категория: excursions
Платформа: Direct
Ссылка: [https://www.trip.com/t/i4gvRtHCsU2](https://www.trip.com/t/i4gvRtHCsU2)
Приоритет: 10
Статус: active

Использовать для:

* `activities_post`
* `weekend_activity`
* `destination_post`

Текст кнопки:

* «Билеты на место»

---

## 7.21. Trip.com Main

Ключ: `trip_main`
Название: Trip.com
Категория: general_travel
Платформа: Direct
Ссылка: [https://www.trip.com/t/Cvio677CsU2](https://www.trip.com/t/Cvio677CsU2)
Приоритет: 5
Статус: active

Использовать для:

* `destination_post`
* `inspiration_story`
* `weekend_trip`
* `general_selection`

Текст кнопки:

* «Trip.com»

---

## 7.22. Trip.com Hotels

Ключ: `trip_hotels`
Название: Trip.com Hotels
Категория: hotels
Платформа: Direct
Ссылка: [https://www.trip.com/t/zwXfl8CCsU2](https://www.trip.com/t/zwXfl8CCsU2)
Приоритет: 8
Статус: active

Использовать для:

* `hotel_post`
* `destination_post`
* `weekend_activity`
* `event_trip`

Текст кнопки:

* «Отели на даты»

---

## 7.23. Trip.com Flights

Ключ: `trip_flights`
Название: Trip.com Flights
Категория: flights
Платформа: Direct
Ссылка: [https://www.trip.com/t/0Uk8kzECsU2](https://www.trip.com/t/0Uk8kzECsU2)
Приоритет: 7
Статус: active

Использовать для:

* `flight_deal`
* `event_trip`
* `weekend_activity`
* `destination_post`

Текст кнопки:

* «Билеты в город»

---

## 7.24. Trip.com Rail

Ключ: `trip_rail`
Название: Trip.com Rail
Категория: ground_transport
Платформа: Direct
Ссылка: [https://www.trip.com/t/PSWgloFCsU2](https://www.trip.com/t/PSWgloFCsU2)
Приоритет: 6
Статус: active

Использовать для:

* `rail_trip`
* `domestic_route`
* `europe_route`

Текст кнопки:

* «ЖД билеты»

---

## 7.25. Trip.com Flight + Hotel

Ключ: `trip_flight_hotel`
Название: Trip.com Flight + Hotel
Категория: general_travel
Платформа: Direct
Ссылка: [https://www.trip.com/t/aw2esuJCsU2](https://www.trip.com/t/aw2esuJCsU2)
Приоритет: 6
Статус: active

Использовать для:

* `weekend_trip`
* `destination_post`
* `family_trip`

Текст кнопки:

* «Перелёт + отель»

---

## 7.26. Trip.com Cars

Ключ: `trip_cars`
Название: Trip.com Cars
Категория: car_rental
Платформа: Direct
Ссылка: [https://www.trip.com/t/pChtUXPCsU2](https://www.trip.com/t/pChtUXPCsU2)
Приоритет: 6
Статус: active

Использовать для:

* `road_trip`
* `destination_post`
* `weekend_activity`

Текст кнопки:

* «Прокат авто»

---

# 8. Переменные Railway

В Railway нужно хранить только секреты, API-ключи и системные настройки.

## Обязательные переменные Railway

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_ID=
TELEGRAM_CHANNEL_ID=
TEST_CHANNEL_ID=

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TEMPERATURE=0.85

PEXELS_API_KEY=

TRAVELPAYOUTS_API_TOKEN=
TRAVELPAYOUTS_MARKER=98526
```

## Не хранить в Railway

Не нужно заносить в Railway все партнёрские ссылки.

В Railway НЕ нужно хранить:

```env
AVIASALES=
OSTROVOK=
TRAVELATA=
CHEREHAPA=
KIWITAXI=
LOCALRENT=
TRIPCOM=
TUTU=
SPUTNIK8=
YANDEX_TRAVEL=
```

Все эти ссылки должны лежать в `configs/services.json`.

---

# 9. Правила выбора ссылок

Правила должны лежать в `configs/link_rules.json`.

## `tour_offer`

Ссылки:

* tours;
* insurance.

Максимум ссылок: 2.
Формат: text_and_button.

---

## `flight_deal`

Ссылки:

* flights;
* hotels.

Максимум ссылок: 2.
Формат: text.

---

## `hotel_post`

Ссылки:

* hotels;
* tours.

Максимум ссылок: 2.
Формат: text.

---

## `destination_post`

Ссылки:

* flights;
* hotels;
* tours.

Максимум ссылок: 2.
Формат: text.

---

## `event_trip`

Ссылки:

* events;
* flights;
* hotels.

Максимум ссылок: 3.
Формат: text.

---

## `weekend_trip`

Ссылки:

* flights;
* hotels;
* tours.

Максимум ссылок: 2.
Формат: text.

---

## `family_trip`

Ссылки:

* tours;
* hotels;
* insurance.

Максимум ссылок: 2.
Формат: text_and_button.

---

## `activities_post`

Ссылки:

* excursions;
* flights;
* hotels.

Максимум ссылок: 3.
Формат: text.

---

## `weekend_activity`

Ссылки:

* excursions;
* flights;
* hotels.

Максимум ссылок: 3.
Формат: text.

---

## `visa_or_residence`

Ссылки:

* foreign_cards;
* insurance.

Максимум ссылок: 1.
Формат: soft_cta.

---

## `payment_abroad`

Ссылки:

* foreign_cards.

Максимум ссылок: 2.
Формат: text.

---

## `practical_travel`

Ссылки:

* foreign_cards;
* insurance.

Максимум ссылок: 1.
Формат: soft_cta.

---

## `inspiration_story`

Ссылки:

* нет.

Максимум ссылок: 0.
Формат: no_partner_link.

---

# 10. Общие правила ссылок

1. Не вставлять ссылку ради галочки.
2. Не перегружать пост 3 и более ссылками без необходимости.
3. Если упомянут конкретный объект, ссылка и фото должны ему соответствовать.
4. Вдохновляющие и narrative-посты часто лучше оставлять без жёсткой монетизации.
5. В одном посте максимум 1–3 кнопки.
6. Если пост полезный и не продающий, CTA может быть «сохраните» или «перешлите», без партнёрской ссылки.
7. Если пост о визах или ВНЖ, не делать агрессивный оффер.
8. Если пост о билетах, можно использовать более прямой CTA.
9. Если пост о туре, можно использовать коммерческий CTA.
10. Если пост о красивом месте, не портить атмосферу чрезмерной продажей.

---

# 11. Как бот ищет темы

## Шаг 1. Обход источников

Бот идёт по источникам по кругу, а не залипает в одном.

Порядок источников:

1. Vandrouki
2. Aviasales Telegram
3. Travelata Telegram
4. ПСЖР / Авиасейлс
5. TravelAsk
6. Журнал Tripster
7. Журнал Яндекс Путешествий
8. Горбилет
9. ПСЖР: концерты мировых звёзд
10. IMIGRATA
11. relocate_easy
12. ekspat_info
13. puteshe
14. Trip.com Activities

`ptuxon` использовать только как ручной стилевой референс.

---

## Шаг 2. Извлечение сигнала

Для каждого сигнала бот должен выделить:

* заголовок;
* ссылку;
* источник;
* дату публикации;
* возможную страну;
* возможный город;
* цену, если есть;
* даты, если есть;
* событие, если есть;
* отель, если есть;
* ключевую мысль;
* возможный жанр;
* возможный CTA;
* уровень свежести.

---

## Шаг 3. Проверка свежести

Тема считается свежей, если:

* дата публикации не старше допустимого срока;
* URL не публиковался ранее;
* заголовок не похож на опубликованный;
* направление не повторялось недавно;
* событие ещё актуально;
* цена или оффер не выглядят устаревшими.

---

## Шаг 4. Дедупликация

Бот проверяет:

* URL;
* заголовок;
* нормализованный заголовок;
* страну;
* город;
* жанр;
* ключевые слова;
* смысловой отпечаток текста;
* hash текста;
* похожие фразы.

Если похожесть высокая — тема пропускается.

---

## Шаг 5. Классификация

Бот определяет:

* основной жанр;
* запасной жанр;
* тип слота;
* уровень продажности;
* допустимые ссылки;
* нужен ли фактчек;
* нужна ли картинка;
* нужна ли кнопка.

---

# 12. Scoring темы

Каждая тема получает оценку от 0 до 100.

| Параметр                | Баллы |
| ----------------------- | ----: |
| Свежесть                |  0–20 |
| Конкретика              |  0–20 |
| Эмоциональный потенциал |  0–15 |
| Потенциал пересылки     |  0–15 |
| Польза                  |  0–10 |
| Реферальная пригодность |  0–10 |
| Соответствие слоту      |  0–10 |

Тема берётся в работу, если score не ниже 60.

Если нет тем выше 60, бот:

1. расширяет список источников;
2. ослабляет привязку к слоту;
3. берёт лучшую тему, но всё равно проверяет дубли.

---

# 13. Ротация тем

Бот не должен публиковать подряд:

* один и тот же жанр;
* одну страну;
* один город;
* один источник;
* один тип CTA;
* одну структуру заголовка;
* одинаковый формат концовки;
* одинаковый тип поста: все подряд продающие или все подряд вдохновляющие.

## Cooldown

Минимальные ограничения:

* тот же жанр — не чаще чем через 2 публикации;
* та же страна — не чаще чем через 3 публикации;
* тот же источник — не чаще чем через 2 публикации, если есть альтернатива;
* визовые и релокационные темы — не подряд;
* офферы — не подряд чаще 2 раз;
* inspiration без пользы — не чаще 1 раза в день.

---

# 14. Что происходит после выбора темы

## Шаг 1. Редакционный планировщик

Бот создаёт карточку:

```json
{
  "source": "",
  "source_url": "",
  "topic": "",
  "genre": "",
  "city": "",
  "country": "",
  "hook_angle": "",
  "target_emotion": "",
  "main_fact": "",
  "practical_value": "",
  "cta_level": "",
  "allowed_services": [],
  "forbidden_claims": [],
  "slot": ""
}
```

## Шаг 2. Генератор

Генерирует 3 варианта:

* вариант 1 — эмоциональный / вдохновляющий;
* вариант 2 — практичный / полезный;
* вариант 3 — продающий / вирусный / вовлекающий.

Для каждого варианта:

* заголовок;
* текст;
* CTA;
* кнопки;
* предупреждения;
* оценка качества.

## Шаг 3. Антишаблонная проверка

Проверяет:

* запрещённые фразы;
* слишком общие формулировки;
* одинаковый ритм;
* похожесть на прошлые посты;
* технические слова;
* отсутствие конкретики;
* слабый заголовок;
* слабую концовку.

## Шаг 4. Фактчек

Проверяет:

* цены;
* даты;
* событие;
* город;
* страну;
* ограничения;
* формулировки риска.

Если факт нельзя подтвердить, бот должен писать осторожно:

* «по данным источника»
* «в подборке указано»
* «сейчас встречаются варианты»
* «перед покупкой лучше проверить даты и условия»

## Шаг 5. CTA engine

Выбирает ссылки и кнопки по `link_rules.json` и `services.json`.

## Шаг 6. Media engine

Подбирает медиа:

1. локальная медиатека;
2. Pexels;
3. fallback-card;
4. без фото только если разрешено.

---

# 15. Prompt-engine

## 15.1. Системный промт редактора

Ты — главный редактор travel Telegram-канала «Мир на ладони».

Ты пишешь на русском языке.

Ты не копируешь источник. Источник — только инфоповод.

Твоя задача — сделать авторский Telegram-пост, который хочется:

* прочитать;
* сохранить;
* переслать;
* обсудить;
* открыть по кнопке, если CTA уместен.

Ты не пишешь шаблонно.

Ты не используешь фразы:

* «Есть направления, которые…»
* «Иногда лучшие поездки…»
* «Если хочется примерить…»
* «Сигнал для…»
* «маршрут реально собрать…»
* «ощущается как полноценная перезагрузка»
* «не когда-нибудь потом»
* «очень вовремя»

Ты не используешь англицизмы без необходимости.

Ты не пишешь внутренние технические слова.

Ты не делаешь каждый пост продающим.

Ты пишешь как опытный travel-редактор, а не как рекламный баннер.

---

## 15.2. Промт редакционного планировщика

На входе есть сигнал из источника.

Определи:

1. Что это за инфоповод.
2. Почему он может быть интересен аудитории.
3. Какой жанр поста подходит.
4. Что в нём важно не потерять.
5. Какая эмоция должна быть у поста.
6. Нужен ли CTA.
7. Какие партнёрские ссылки допустимы.
8. Что нельзя утверждать без проверки.
9. Какие 3 угла подачи можно сделать.

---

## 15.3. Промт генератора 3 вариантов

Сгенерируй 3 разных Telegram-поста.

Требования:

* каждый вариант должен быть самостоятельным;
* варианты не должны повторять друг друга;
* не использовать шаблонные фразы;
* не писать «воду»;
* не использовать англицизмы;
* не копировать источник;
* не вставлять технические слова;
* использовать короткие абзацы;
* заголовок должен цеплять;
* концовка должна быть законченной;
* CTA только если уместен.

---

## 15.4. Промт антишаблонного редактора

Проверь текст.

Если найдено:

* шаблонная фраза;
* общие слова без конкретики;
* повтор;
* слабая концовка;
* внутренние технические слова;
* похожесть на старые посты;
* рекламный перегруз;
* нет повода читать дальше;

перепиши текст полностью.

---

## 15.5. Промт выбора лучшего варианта для автопостинга

Оцени 3 варианта по шкале 0–100:

* заголовок;
* конкретика;
* живой язык;
* Telegram-ритм;
* вовлечение;
* польза;
* уместность CTA;
* отсутствие шаблонности;
* отличие от прошлых постов.

Выбери лучший вариант.

Если лучший вариант ниже 75 — сгенерируй новый.

---

# 16. Оформление Telegram-поста

## Заголовок

Требования:

* 1 строка;
* без канцелярита;
* без мусорного кликбейта;
* без англицизмов;
* конкретный;
* цепляющий.

Примеры:

* «РЖД тестируют доставку багажа: маленькая новость, которая может заметно облегчить поездки»
* «Анталья за цену ужина — тот случай, когда море становится ближе»
* «Стамбул на выходные снова выглядит слишком хорошей идеей»
* «Отель, где отпуск начинается ещё до заселения»

---

## Первый абзац

Должен:

* объяснить, почему это важно;
* не повторять заголовок;
* не быть общим;
* не начинаться с «Есть направления…».

---

## Тело поста

Правила:

* короткие абзацы;
* 1 мысль = 1 абзац;
* без стены текста;
* 1–3 эмодзи максимум;
* списки только если они помогают;
* конкретика важнее красивостей.

---

## Концовка

Должна быть:

* логичной;
* человеческой;
* не шаблонной;
* не одинаковой в каждом посте.

Варианты концовок:

* вопрос;
* мягкий CTA;
* предложение сохранить;
* предложение переслать;
* короткое резюме;
* без CTA, если пост вдохновляющий.

---

# 17. Эмодзи

Допустимые:

* ✈️ перелёты
* 🏨 отели
* 🌊 море
* 🧳 багаж
* 🎟 события
* 🗺 маршруты
* 💬 обсуждение
* 🔥 горящее
* 🚆 поезд
* 🚕 трансфер
* 🛡 страховка

Нельзя:

* ставить эмодзи в каждой строке;
* делать из поста рекламную листовку;
* использовать эмодзи вместо смысла.

---

# 18. Как вовлекать подписчиков

Бот должен иногда использовать:

* вопросы;
* мини-выбор;
* «сохраните»;
* «перешлите тому, кто…»;
* «вы бы поехали?»;
* «что выбрали бы?»;
* «поставьте реакцию, если…».

Но не в каждом посте.

Примеры:

* «Сохранили бы такой маршрут на выходные?»
* «Перешлите тому, кто вечно собирает чемодан в последний момент.»
* «Если даты совпадают — лучше проверить сразу, такие цены долго не живут.»
* «Что выбрали бы: море на пару дней или город на 20 000 шагов?»

---

# 19. Запрещённые фразы

Бот никогда не должен писать:

* «Есть направления, которые…»
* «Иногда лучшие поездки…»
* «Если хочется примерить…»
* «Сигнал для…»
* «маршрут реально собрать…»
* «очень вовремя совпадают…»
* «не когда-нибудь потом…»
* «ощущается как полноценная перезагрузка»
* «с любовью, ваш…» в каждом посте
* «путешествие мечты» без смысла
* «локация»
* «вайб»
* «must visit»
* «релакс»
* «чилл»
* «топчик»
* «инстаграмный»
* «Pinterest»
* «wow-эффект»

Если найдена хотя бы одна запрещённая фраза, вариант бракуется.

---

# 20. Проверка «запаха ИИ»

Бот должен проверять:

* одинаковую длину абзацев;
* слишком симметричные предложения;
* абстрактные слова без фактов;
* повторяющиеся вступления;
* повторяющиеся концовки;
* чрезмерно гладкий рекламный стиль;
* отсутствие конкретной детали;
* фразы, которые можно поставить в любой travel-пост.

Если текст можно вставить в любой другой пост без потери смысла — текст плохой и должен быть переписан.

---

# 21. Хранение состояния

Бот должен хранить:

```json
{
  "published_urls": [],
  "published_titles": [],
  "published_text_hashes": [],
  "published_semantic_fingerprints": [],
  "published_topics": [],
  "published_genres": [],
  "published_countries": [],
  "published_cities": [],
  "published_sources": [],
  "last_slot": "",
  "last_cta_type": "",
  "rejected_topics": [],
  "successful_patterns": [],
  "failed_patterns": []
}
```

---

# 22. Команды Telegram-бота

## Основные команды

```text
/start
/version
/test
/preview
/publish
/rewrite
/softer
/sales
/reject
/autopost_on
/autopost_off
/schedule
/status
/last
/why_skipped
/sources
/topics
/services
```

---

## `/test`

Ручной тест:

* ищет тему;
* генерирует 3 варианта;
* показывает админу;
* даёт кнопки выбора.

---

## `/preview`

Показывает:

* источник;
* жанр;
* score;
* почему тема выбрана;
* 3 варианта;
* ссылки;
* предупреждения.

---

## `/publish`

Публикует выбранный вариант.

---

## `/autopost_on`

Включает автопостинг.

---

## `/autopost_off`

Выключает автопостинг.

---

## `/why_skipped`

Показывает, почему последняя тема была пропущена.

---

# 23. Архитектура кода

```text
telegram-botmir-v2/
├── src/
│   ├── telegram_app.py
│   ├── config_loader.py
│   ├── source_manager.py
│   ├── signal_extractor.py
│   ├── topic_classifier.py
│   ├── scoring_engine.py
│   ├── rotation_engine.py
│   ├── dedup_engine.py
│   ├── editorial_planner.py
│   ├── ai_writer.py
│   ├── quality_selector.py
│   ├── anti_template_checker.py
│   ├── fact_checker.py
│   ├── cta_engine.py
│   ├── media_engine.py
│   ├── publisher.py
│   ├── scheduler.py
│   ├── state_store.py
│   └── analytics_store.py
├── configs/
│   ├── topics.json
│   ├── sources.json
│   ├── services.json
│   ├── link_rules.json
│   ├── editorial_policy.json
│   └── forbidden_phrases.json
├── prompts/
│   ├── system_editor_ru.md
│   ├── editorial_planner_ru.md
│   ├── writer_3_variants_ru.md
│   ├── anti_template_ru.md
│   ├── quality_selector_ru.md
│   ├── cta_rules_ru.md
│   └── fact_check_ru.md
├── data/
│   ├── state.json
│   ├── publication_log.json
│   ├── rejected_topics.json
│   └── analytics.json
├── docs/
│   ├── README.md
│   ├── CHECKLIST.md
│   ├── TOPICS.md
│   ├── SOURCES.md
│   └── SERVICES.md
├── tests/
│   └── validate_project.py
├── requirements.txt
├── README.md
└── .env.example
```

---

# 24. Что категорически не должно быть в финальном проекте

В финальном проекте не должно быть:

* старого `draft_writer.py`, если он содержит шаблоны;
* старого `style_editor.py`, если он перетирает GPT-текст;
* старых snapshots;
* `.pyc`;
* `__pycache__`;
* `download`;
* архивов внутри архива;
* старых `.py` файлов в корне;
* битой кодировки;
* русских текстов в `requirements.txt`;
* переменных окружения в `requirements.txt`;
* старых шаблонных фраз.

---

# 25. `requirements.txt`

Файл должен содержать только библиотеки, построчно:

```txt
python-telegram-bot>=21.0
openai>=1.30.0
python-dotenv>=1.0.1
requests>=2.31.0
beautifulsoup4>=4.12.3
lxml>=5.2.1
apscheduler>=3.10.4
feedparser>=6.0.11
Pillow>=10.3.0
```

---

# 26. Проверочный скрипт

В проекте должен быть `tests/validate_project.py`.

Он должен проверять:

1. `requirements.txt`:

   * только библиотеки;
   * нет `TELEGRAM_BOT_TOKEN`;
   * нет русских фраз;
   * нет одной длинной строки.

2. Код:

   * все `src/*.py` компилируются;
   * нет запрещённых фраз;
   * нет битой кодировки;
   * нет старого draft writer.

3. JSON:

   * все JSON читаются;
   * есть sources;
   * есть services;
   * есть link rules;
   * есть topics.

4. Структуру:

   * нет `.pyc`;
   * нет `__pycache__`;
   * нет `download`;
   * нет старых файлов в корне.

5. Логику:

   * `/version` содержит финальную версию;
   * `/test` должен генерировать 3 варианта;
   * автопостинг должен публиковать 1 лучший вариант.

---

# 27. Как должен работать автопостинг

Автопостинг:

1. Определяет текущий слот.
2. Выбирает допустимые жанры.
3. Обходит источники.
4. Извлекает сигналы.
5. Отбрасывает старые.
6. Отбрасывает повторы.
7. Считает score.
8. Выбирает лучшую тему.
9. Генерирует 3 варианта.
10. Проверяет каждый вариант.
11. Выбирает лучший вариант.
12. Вставляет CTA.
13. Подбирает медиа.
14. Публикует.
15. Записывает в историю.

---

# 28. Как должен работать ручной тест

`/test`:

1. Бот ищет тему.
2. Показывает админу:

   * источник;
   * ссылку;
   * жанр;
   * score;
   * почему тема выбрана.
3. Генерирует 3 варианта.
4. Показывает их.
5. Даёт кнопки:

   * опубликовать вариант 1;
   * опубликовать вариант 2;
   * опубликовать вариант 3;
   * переписать;
   * сделать мягче;
   * сделать продающе;
   * отклонить.

---

# 29. Критерии готовности финальной версии

Финальная версия считается готовой, если:

1. `/version` показывает финальную версию.
2. `/test` выдаёт 3 разных варианта.
3. Ни один вариант не содержит старых шаблонов.
4. В автопостинге публикуется 1 лучший вариант.
5. Темы чередуются.
6. Источники чередуются.
7. Одинаковые посты не повторяются.
8. Ссылки вставляются по правилам.
9. Вдохновляющие посты могут выходить без ссылок.
10. Офферы получают правильные кнопки.
11. Визы и карты получают мягкий CTA.
12. Посты не обрезаются.
13. Фото и текст отправляются безопасно.
14. Нет битой кодировки.
15. `requirements.txt` чистый.
16. Старых файлов нет.
17. Проверочный скрипт проходит без ошибок.

---

# 30. Главный принцип разработки

Не латать старый бот.

Не переносить старые шаблоны.

Не использовать старые тексты.

Из старого проекта можно брать только:

* список источников;
* список тем;
* список сервисов;
* реферальные ссылки;
* правила ссылок.

Всё остальное должно быть написано заново.

---

# 31. Финальная формула работы бота

```text
Свежий источник
→ сигнал
→ очистка
→ проверка свежести
→ дедупликация
→ классификация жанра
→ скоринг
→ выбор темы
→ редакционный план
→ 3 варианта GPT
→ антишаблонная проверка
→ фактчек
→ выбор CTA
→ подбор ссылок
→ подбор медиа
→ ручной выбор или автоселектор
→ публикация
→ запись в память
→ аналитика
→ улучшение будущих публикаций
```

---

# 32. Самое главное требование

Бот должен перестать писать как старый шаблонный генератор.

Он должен писать так, будто за каналом стоит живой travel-редактор, который:

* понимает аудиторию;
* умеет выбрать инфоповод;
* умеет сделать из новости красивый пост;
* знает, когда продавать;
* знает, когда не продавать;
* умеет вовлекать;
* не повторяется;
* не пишет воду;
* не портит канал одинаковыми постами.
