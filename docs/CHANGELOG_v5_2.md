# CHANGELOG v5.2 LINK_MEDIA_FLIGHT_FIX

Исправлены 5 ключевых файлов:

1. `src/cta_engine.py` — запрещены ссылки на чужие Telegram-каналы для flight_deal; первая кнопка ведёт на поиск билетов.
2. `src/media_engine.py` — для flight_deal создаётся карточка оффера вместо доверия случайной картинке из Telegram.
3. `src/signal_extractor.py` — улучшено распознавание маршрутов и дат.
4. `configs/cities_iata.json` — добавлены/уточнены IATA для маршрутов.
5. `configs/city_aliases.json` — добавлены алиасы городов.

Дополнительно обновлён `src/version.py`, чтобы `/version` показывал новую сборку.
