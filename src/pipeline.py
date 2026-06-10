from __future__ import annotations

from typing import Any

from .ai_writer import AIWriter
from .analytics_store import AnalyticsStore
from .config_loader import Settings, load_settings
from .cta_engine import CTAEngine
from .dedup_engine import DedupEngine
from .diagnostics import RunReport
from .editorial_brief_engine import EditorialBriefEngine
from .engagement_engine import EngagementEngine
from .fact_checker import FactChecker
from .fallback_topic_engine import FallbackTopicEngine
from .media_engine import MediaEngine
from .media_sources import MediaSources
from .models import Brief, PreparedPost, PostVariant, Signal
from .openai_client import OpenAIClient
from .publisher import Publisher
from .quality_selector import QualitySelector
from .rotation_engine import RotationEngine
from .scoring_engine import ScoringEngine
from .signal_extractor import SignalExtractor
from .source_health import SourceHealthStore
from .source_manager import SourceManager
from .source_registry import SourceRegistry
from .state_store import StateStore
from .telegram_post_writer import TelegramPostWriter
from .text_utils import now_iso
from .topic_classifier import TopicClassifier
from .topic_guard import TopicGuard


class EditorialPipeline:
    def __init__(self, settings: Settings | None = None, bot=None):
        self.settings = settings or load_settings()
        self.state = StateStore()
        self.analytics = AnalyticsStore()
        self.health = SourceHealthStore()
        self.registry = SourceRegistry()
        self.sources = SourceManager(self.registry, self.health)
        self.fallback = FallbackTopicEngine()
        self.guard = TopicGuard()
        self.extractor = SignalExtractor()
        self.classifier = TopicClassifier()
        self.scorer = ScoringEngine()
        self.dedup = DedupEngine(self.state)
        self.rotation = RotationEngine(self.state)
        self.brief_engine = EditorialBriefEngine()
        self.openai = OpenAIClient(self.settings)
        self.writer = AIWriter(self.openai, local_fallback=self.settings.local_writer_fallback)
        self.engagement = EngagementEngine()
        self.fact = FactChecker()
        self.quality = QualitySelector()
        self.media = MediaEngine(MediaSources(self.settings))
        self.post_writer = TelegramPostWriter()
        self.publisher = Publisher(bot)
        self.cta = CTAEngine(channel_url=self._channel_url())

    def _channel_url(self) -> str:
        if self.settings.channel_public_url:
            return self.settings.channel_public_url
        ch = self.settings.telegram_channel_id
        if ch.startswith("@"):
            return "https://t.me/" + ch.lstrip("@")
        return ""

    async def collect_candidates(self, report: RunReport, test_index: int = 0) -> list[Signal]:
        current_slot = self.classifier.current_slot()
        raw, errors = await self.sources.collect(limit_per_source=4)
        report.source_errors.update(errors)
        report.count("sources_checked", len(self.registry.active_sources()))
        health = self.health.load()
        report.count("sources_ok", sum(1 for x in health.values() if x.get("ok")))
        report.count("source_errors", len(errors))
        report.count("signals_found", len(raw))
        report.step("sources.collect", "ok", {"signals": len(raw), "errors": len(errors)})

        if not raw and self.settings.allow_fallback_autopublish:
            raw = [self.fallback.generate(current_slot, test_index)]
            report.step("fallback.generate", "ok", raw[0].title)
        elif not raw:
            report.step("fallback.generate", "skip", "fallback disabled")

        guarded = []
        for s in raw:
            ok, reason = self.guard.allow(s)
            if ok:
                guarded.append(s)
            else:
                self._remember_rejected(s, reason)
        report.count("after_guard", len(guarded))
        report.step("topic_guard.filter", "ok", len(guarded))
        if not guarded and self.settings.allow_fallback_autopublish:
            guarded = [self.fallback.generate(current_slot, test_index + 1)]
            report.step("fallback.after_guard", "ok", guarded[0].title)

        enriched = []
        for s in guarded:
            s = self.extractor.enrich(s)
            s = self.classifier.classify(s)
            s = self.scorer.score(s, current_slot=current_slot)
            enriched.append(s)
        report.step("extract_classify_score", "ok", len(enriched))

        unique = self.dedup.filter(enriched)
        report.count("after_dedup", len(unique))
        if not unique and self.settings.allow_fallback_autopublish:
            unique = [self.scorer.score(self.classifier.classify(self.extractor.enrich(self.fallback.generate(current_slot, test_index + 2))), current_slot=current_slot)]
            report.step("fallback.after_dedup", "ok", unique[0].title)

        ranked = self.rotation.rank(unique, current_slot=current_slot, test_index=test_index)
        report.count("candidates", len(ranked))
        report.step("rotation.rank", "ok", [s.title for s in ranked[:3]])
        return ranked

    async def prepare_post(self, test_index: int = 0) -> tuple[PreparedPost | None, RunReport]:
        report = RunReport()
        candidates = await self.collect_candidates(report, test_index=test_index)
        if not candidates:
            report.finish("error", "Нет кандидатов и fallback не сработал")
            return None, report
        signal = candidates[0]
        brief = self.brief_engine.build(signal)
        variants, best_id, writer_warnings = await self.writer.generate(brief)
        report.count("gpt_variants", len(variants))
        if writer_warnings:
            report.count("openai_error", 1)
            report.step("ai_writer.generate", "error", writer_warnings)
        else:
            report.count("openai_ok", 1)
            report.step("ai_writer.generate", "ok", {"provider": "OpenAI", "variants": len(variants)})
        if not variants:
            report.finish("error", "OpenAI не выдал валидный пост. Локальный генератор отключён, публикации не будет.")
            return None, report

        processed: list[PostVariant] = []
        for v in variants:
            v = self.engagement.improve(v, brief)
            v = self.fact.check(v, brief)
            v = self.cta.apply(v, brief)
            processed.append(v)
        best, scored = self.quality.choose(processed, brief)
        if not best:
            report.finish("error", "Quality gate отклонил пост ниже минимального качества")
            return None, report
        media = self.media.find_or_generate(brief, best)
        report.count("media", 1 if media and (media.path or media.url) else 0)
        report.step("media.find_or_generate", "ok", media.to_dict() if media else {})
        session_id = self.state.new_session_id()
        prepared = PreparedPost(session_id=session_id, signal=signal, brief=brief, variants=scored, best_variant_id=best.variant_id, media=media, diagnostics=report.to_dict())
        self.state.save_session(prepared.to_dict())
        report.finish("prepared", f"Подготовлено: {best.title}")
        return prepared, report

    async def publish_prepared(self, prepared: PreparedPost, variant_id: int | None = None, channels: list[str] | None = None, dry_run: bool = False) -> tuple[dict[str, Any], RunReport]:
        report = RunReport()
        variant = prepared.best_variant()
        if variant_id is not None:
            for v in prepared.variants:
                if v.variant_id == variant_id:
                    variant = v
                    break
        formatted = self.post_writer.format(variant, prepared.brief, with_media=bool(prepared.media and (prepared.media.path or prepared.media.url)))
        channels = channels or self.state.channels(self.settings.telegram_channel_id)
        result = await self.publisher.publish(channels, formatted, variant.buttons, prepared.media, dry_run=dry_run)
        published_ok = sum(1 for r in result.values() if r.get("ok"))
        report.count("published", published_ok)
        report.step("publisher.publish", "ok" if published_ok else "error", result)
        if published_ok:
            self._remember_publication(prepared.signal, variant, result)
            if prepared.signal.is_fallback:
                self.fallback.remember(prepared.signal, variant.title)
            self.analytics.record("published", {"title": variant.title, "genre": prepared.brief.genre, "channels": channels})
            report.finish("published", f"Опубликовано: {variant.title}")
        else:
            report.finish("error", "Публикация не состоялась")
        state = self.state.load()
        state["last_run"] = report.to_dict()
        state["last_result"] = report.result
        self.state.save(state)
        return result, report

    async def run_once(self, channels: list[str] | None = None, dry_run: bool = False) -> tuple[PreparedPost | None, dict[str, Any], RunReport]:
        prepared, prep_report = await self.prepare_post()
        if not prepared:
            state = self.state.load(); state["last_run"] = prep_report.to_dict(); state["last_result"] = prep_report.result; self.state.save(state)
            return None, {}, prep_report
        result, pub_report = await self.publish_prepared(prepared, channels=channels, dry_run=dry_run)
        # объединяем краткие счётчики для отчёта админу
        prep_report.counters.update(pub_report.counters)
        prep_report.steps.extend(pub_report.steps)
        prep_report.finish(pub_report.result, pub_report.message)
        state = self.state.load(); state["last_run"] = prep_report.to_dict(); state["last_result"] = prep_report.result; self.state.save(state)
        return prepared, result, prep_report

    def _remember_publication(self, signal: Signal, variant: PostVariant, result: dict[str, Any]) -> None:
        self.state.append_publication({
            "published_at": now_iso(),
            "title": variant.title,
            "url": signal.url,
            "source_key": signal.source_key,
            "source_name": signal.source_name,
            "genre": signal.genre,
            "slot": signal.slot,
            "city": signal.city,
            "country": signal.country,
            "semantic_hash": signal.semantic_hash,
            "channels_result": result,
        })

    def _remember_rejected(self, signal: Signal, reason: str) -> None:
        from .config_loader import DATA_DIR, load_json, save_json
        data = load_json(DATA_DIR / "rejected_topics.json", default=[])
        data.append({"time": now_iso(), "title": signal.title, "source_key": signal.source_key, "reason": reason})
        save_json(DATA_DIR / "rejected_topics.json", data[-500:])
