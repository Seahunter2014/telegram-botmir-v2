from __future__ import annotations

from typing import Any

from .ai_writer import AIWriter, MASTER_PROMPT_FILE
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
from .models import PreparedPost, PostVariant, Signal
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
        self.writer = AIWriter(self.openai, local_fallback=False)
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
        report.step("rotation.rank", "ok", [s.title for s in ranked[:5]])
        return ranked

    async def prepare_post(self, test_index: int = 0, remember_preview: bool = True) -> tuple[PreparedPost | None, RunReport]:
        report = RunReport()
        candidates = await self.collect_candidates(report, test_index=test_index)
        current_slot = self.classifier.current_slot()

        # Автопостинг не должен останавливаться, если сильная живая тема не прошла Quality Gate.
        # Поэтому к реальным кандидатам всегда добавляем резерв evergreen/fallback-тем: они проходят тот же OpenAI + Quality Gate,
        # но дают боту запас тем для публикации вместо пустого отчёта.
        reserve: list[Signal] = []
        if self.settings.allow_fallback_autopublish:
            for i in range(8):
                fb = self.fallback.generate(current_slot, test_index + 100 + i)
                fb = self.extractor.enrich(fb)
                fb = self.classifier.classify(fb)
                fb = self.scorer.score(fb, current_slot=current_slot)
                reserve.append(fb)
            candidates = list(candidates) + reserve
            report.step("fallback.reserve", "ok", {"added": len(reserve), "topics": [x.title for x in reserve[:5]]})

        if not candidates:
            report.finish("error", "Нет кандидатов и fallback не сработал")
            return None, report

        max_candidates = min(len(candidates), 14)
        max_rewrite_attempts = 8
        last_scored: list[PostVariant] = []
        last_signal: Signal | None = None
        last_brief = None

        for candidate_no, signal in enumerate(candidates[:max_candidates], 1):
            last_signal = signal
            brief = self.brief_engine.build(signal)
            last_brief = brief
            report.step("generation.context", "ok", {
                "candidate_no": candidate_no,
                "source_name": signal.source_name,
                "source_key": signal.source_key,
                "source_url": signal.source_url,
                "topic": brief.topic,
                "genre": brief.genre,
                "slot": brief.slot,
                "signal_score": signal.score,
                "editorial_angle": brief.editorial_angle,
                "practical_value": brief.practical_value,
                "main_fact": brief.main_fact,
            })

            previous_bad: PostVariant | None = None
            for attempt in range(1, max_rewrite_attempts + 1):
                if attempt == 1 or previous_bad is None:
                    variants, best_id, writer_warnings = await self.writer.generate(brief)
                    generation_action = "generate"
                else:
                    feedback = self.quality.feedback_for_rewrite(previous_bad)
                    variants, best_id, writer_warnings = await self.writer.improve(brief, previous_bad, feedback, attempt)
                    generation_action = "improve"

                report.count("gpt_variants", report.counters.get("gpt_variants", 0) + len(variants))
                if writer_warnings:
                    report.count("openai_error", report.counters.get("openai_error", 0) + 1)
                    report.step("ai_writer.generate", "error", {
                        "provider": "OpenAI",
                        "model": self.settings.openai_model,
                        "prompt_file": MASTER_PROMPT_FILE,
                        "candidate_no": candidate_no,
                        "attempt": attempt,
                        "action": generation_action,
                        "warnings": writer_warnings,
                    })
                else:
                    report.count("openai_ok", report.counters.get("openai_ok", 0) + 1)
                    report.step("ai_writer.generate", "ok", {
                        "provider": "OpenAI",
                        "model": self.settings.openai_model,
                        "prompt_file": MASTER_PROMPT_FILE,
                        "candidate_no": candidate_no,
                        "attempt": attempt,
                        "action": generation_action,
                        "variants": len(variants),
                    })
                if not variants:
                    break

                processed: list[PostVariant] = []
                for v in variants:
                    v = self.engagement.improve(v, brief)
                    v = self.fact.check(v, brief)
                    v = self.cta.apply(v, brief)
                    processed.append(v)
                if processed:
                    report.step("cta.apply", "ok", {"buttons": [b.text for b in processed[0].buttons]})

                best, scored = self.quality.choose(processed, brief)
                last_scored = scored
                top = scored[0] if scored else None
                if best:
                    report.step("quality.gate", "ok", {
                        "decision": "publishable",
                        "score": best.score,
                        "title": best.title,
                        "reasons": best.why_it_works,
                        "warnings": best.warnings,
                        "candidate_no": candidate_no,
                        "attempt": attempt,
                        "rewrite_attempts": attempt - 1,
                    })
                    media = self.media.find_or_generate(brief, best)
                    report.count("media", 1 if media and (media.path or media.url) else 0)
                    report.step("media.find_or_generate", "ok", media.to_dict() if media else {})

                    session_id = self.state.new_session_id()
                    prepared = PreparedPost(
                        session_id=session_id,
                        signal=signal,
                        brief=brief,
                        variants=scored,
                        best_variant_id=best.variant_id,
                        media=media,
                        diagnostics=report.to_dict(),
                    )
                    self.state.save_session(prepared.to_dict())
                    if remember_preview:
                        self.state.remember_preview(signal, best.title)
                    report.finish("prepared", f"Подготовлено: {best.title}")
                    return prepared, report

                if top:
                    previous_bad = top
                    report.step("quality.gate", "rewrite", {
                        "decision": "rewrite",
                        "score": top.score,
                        "title": top.title,
                        "reasons": top.why_it_works,
                        "warnings": top.warnings,
                        "candidate_no": candidate_no,
                        "attempt": attempt,
                        "next_action": "переписать этот же пост и повысить качество",
                    })
                    continue
                break

            self._remember_rejected(signal, f"не удалось поднять качество до {self.quality.min_score} после {max_rewrite_attempts} попыток")
            report.step("candidate.skip_after_rewrites", "skip", {
                "candidate_no": candidate_no,
                "topic": signal.title,
                "reason": f"не удалось поднять качество до {self.quality.min_score}",
            })

        # Последний аварийный редакционный цикл: если все темы не вытянулись, берём чистую evergreen-тему
        # и просим OpenAI написать пост с жёстким feedback. Это не локальная болванка, а последняя попытка OpenAI.
        if self.settings.allow_fallback_autopublish:
            emergency = self.fallback.generate(current_slot, test_index + 999)
            emergency = self.scorer.score(self.classifier.classify(self.extractor.enrich(emergency)), current_slot=current_slot)
            brief = self.brief_engine.build(emergency)
            previous_bad = last_scored[0] if last_scored else None
            report.step("emergency_fallback.start", "ok", {"topic": emergency.title})
            for attempt in range(1, 9):
                if previous_bad is None:
                    variants, best_id, writer_warnings = await self.writer.generate(brief)
                    action = "generate"
                else:
                    feedback = self.quality.feedback_for_rewrite(previous_bad) + "\nЭто аварийная попытка автопостинга: пост должен быть опубликован, но только если станет качественным, конкретным и красиво оформленным."
                    variants, best_id, writer_warnings = await self.writer.improve(brief, previous_bad, feedback, attempt)
                    action = "improve"
                report.count("gpt_variants", report.counters.get("gpt_variants", 0) + len(variants))
                report.step("emergency_fallback.openai", "error" if writer_warnings else "ok", {"attempt": attempt, "action": action, "warnings": writer_warnings})
                if not variants:
                    break
                processed = []
                for v in variants:
                    v = self.engagement.improve(v, brief)
                    v = self.fact.check(v, brief)
                    v = self.cta.apply(v, brief)
                    processed.append(v)
                best, scored = self.quality.choose(processed, brief)
                last_scored = scored
                if best:
                    media = self.media.find_or_generate(brief, best)
                    report.count("media", 1 if media and (media.path or media.url) else 0)
                    report.step("emergency_fallback.quality", "ok", {"score": best.score, "title": best.title, "attempt": attempt})
                    report.step("media.find_or_generate", "ok", media.to_dict() if media else {})
                    session_id = self.state.new_session_id()
                    prepared = PreparedPost(
                        session_id=session_id,
                        signal=emergency,
                        brief=brief,
                        variants=scored,
                        best_variant_id=best.variant_id,
                        media=media,
                        diagnostics=report.to_dict(),
                    )
                    self.state.save_session(prepared.to_dict())
                    if remember_preview:
                        self.state.remember_preview(emergency, best.title)
                    report.finish("prepared", f"Подготовлено через emergency fallback: {best.title}")
                    return prepared, report
                previous_bad = scored[0] if scored else previous_bad

        top = last_scored[0] if last_scored else None
        if top:
            report.step("quality.gate", "reject", {
                "decision": "reject",
                "score": top.score,
                "title": top.title,
                "reasons": top.why_it_works,
                "warnings": top.warnings,
            })
        report.finish("error", f"Не удалось получить пост качества {self.quality.min_score}+ после перебора тем и переписываний")
        return None, report

    async def publish_prepared(self, prepared: PreparedPost, variant_id: int | None = None, channels: list[str] | None = None, dry_run: bool = False) -> tuple[dict[str, Any], RunReport]:
        report = RunReport()
        previous = prepared.diagnostics or {}
        if isinstance(previous, dict):
            report.steps.extend(previous.get("steps") or [])
            report.counters.update(previous.get("counters") or {})
            report.source_errors.update(previous.get("source_errors") or {})

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
        post_ids = [str(v.get("post_id")) for v in result.values() if isinstance(v, dict) and v.get("post_id")]
        post_urls = [str(v.get("post_url")) for v in result.values() if isinstance(v, dict) and v.get("post_url")]
        if published_ok:
            report.step("publication.summary", "ok", {
                "title": variant.title,
                "score": variant.score,
                "post_ids": post_ids,
                "post_urls": post_urls,
                "rating_command": f"/rate {post_ids[0]} 10" if post_ids else "/rate НОМЕР_ПОСТА 10",
            })
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
        prepared, prep_report = await self.prepare_post(remember_preview=True)
        if not prepared:
            state = self.state.load(); state["last_run"] = prep_report.to_dict(); state["last_result"] = prep_report.result; self.state.save(state)
            return None, {}, prep_report
        result, pub_report = await self.publish_prepared(prepared, channels=channels, dry_run=dry_run)
        state = self.state.load(); state["last_run"] = pub_report.to_dict(); state["last_result"] = pub_report.result; self.state.save(state)
        return prepared, result, pub_report

    def _remember_publication(self, signal: Signal, variant: PostVariant, result: dict[str, Any]) -> None:
        post_ids = [str(v.get("post_id")) for v in result.values() if isinstance(v, dict) and v.get("post_id")]
        post_urls = [str(v.get("post_url")) for v in result.values() if isinstance(v, dict) and v.get("post_url")]
        self.state.append_publication({
            "published_at": now_iso(),
            "post_id": post_ids[0] if post_ids else "",
            "post_url": post_urls[0] if post_urls else "",
            "quality_score": variant.score,
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
