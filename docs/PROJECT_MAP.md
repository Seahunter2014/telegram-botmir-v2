# Карта проекта v6.2

## Цель
AI-редакция travel-канала «Мир на ладони»: найти повод, выбрать угол, написать хороший Telegram-пост, подобрать CTA/медиа, опубликовать, записать историю и отчитаться админу.

## Основной pipeline

```text
/run_once или scheduler
→ diagnostics.start_run
→ source_manager.collect
→ source_health.update
→ fallback_topic_engine.generate при необходимости
→ topic_guard.filter
→ signal_extractor.enrich
→ topic_classifier.classify
→ scoring_engine.score
→ dedup_engine.filter
→ rotation_engine.rank
→ editorial_brief_engine.build
→ ai_writer.generate
→ engagement_engine.improve
→ fact_checker.check
→ cta_engine.apply
→ quality_selector.choose
→ media_engine.find_or_generate
→ telegram_post_writer.format
→ publisher.publish
→ state_store/publication_log
→ diagnostics.finish
```

## Главные связи

- `telegram_app.py` принимает команды Telegram и вызывает `EditorialPipeline`.
- `pipeline.py` связывает все редакционные модули.
- `source_manager.py` собирает сигналы из `configs/sources.json`.
- `fallback_topic_engine.py` берёт темы из `configs/fallback_topics.json`, если источники недоступны.
- `cta_engine.py` использует `configs/services.json` и `configs/link_rules.json`.
- `media_engine.py` ищет медиа через `media_sources.py` или генерирует fallback через `image_generation.py`.
- `telegram_post_writer.py` форматирует и делит длинные посты на 2 части.
- `publisher.py` публикует в каналы и делает retry/fallback.
- `state_store.py` хранит состояние, каналы, сессии и историю.
- `diagnostics.py` формирует отчёт по каждому запуску.
