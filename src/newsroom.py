from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from .ai_writer import ensure_quality_or_raise, generate_variants
from .cta_engine import select_cta
from .dedup_engine import is_duplicate_signal
from .editorial_planner import plan_post
from .media_engine import choose_media
from .quality_selector import score_variant, select_best_variant
from .rotation_engine import current_slot
from .scoring_engine import score_signal
from .source_manager import collect_signals
from .state_store import record_selection, record_skip
from .topic_classifier import classify_signal


def candidate_pool(bundle: Any, forced_slot: str | None = None) -> list[dict]:
    slot = current_slot(bundle.policy, forced_slot)
    pool: list[dict] = []
    for signal in collect_signals(bundle):
        is_duplicate, _reason = is_duplicate_signal(signal)
        if is_duplicate:
            continue
        topic = classify_signal(signal, bundle, slot)
        score = score_signal(signal, topic, slot, bundle)
        if score["score"] < int(bundle.policy.get("minimum_score", 60)):
            continue
        pool.append({"signal": signal, "topic": topic, "score": score, "slot": slot})
    return sorted(pool, key=lambda item: item["score"]["score"], reverse=True)


def _build_variant_set(bundle: Any, plan: dict, signal: dict) -> tuple[list[dict], dict]:
    cta = select_cta(plan, bundle)
    variants = generate_variants(plan, signal, bundle)
    ensure_quality_or_raise(variants, bundle)
    scored: list[dict] = []
    for variant in variants:
        variant["buttons"] = cta.get("buttons", [])
        variant["quality"] = score_variant(variant, plan, bundle)
        scored.append(variant)
    best = select_best_variant(scored, plan, bundle)
    return scored, best


def create_package(
    bundle: Any,
    forced_topic: str | None = None,
    forced_slot: str | None = None,
    allow_media: bool = True,
    require_minimum_quality: bool = False,
) -> dict:
    pool = candidate_pool(bundle, forced_slot)
    if forced_topic:
        pool = [item for item in pool if item["topic"] == forced_topic] or pool
    if not pool:
        record_skip("no_fresh_candidate", "Нет свежих тем после фильтров")
        raise RuntimeError("Не найдено свежих тем: источники недоступны, устарели или отфильтрованы дедупликацией.")

    selected = pool[0]
    signal = selected["signal"]
    topic = selected["topic"]
    slot = selected["slot"]
    plan = plan_post(signal, topic, selected["score"], slot, bundle)

    min_quality = int(bundle.policy.get("autopost_minimum_variant_score", 75))
    attempts = 3 if require_minimum_quality else 1
    last_best: dict | None = None
    last_variants: list[dict] = []
    for attempt in range(1, attempts + 1):
        variants, best = _build_variant_set(bundle, plan, signal)
        last_variants = variants
        last_best = best
        if not require_minimum_quality or best["quality"]["score"] >= min_quality:
            break
        record_skip(
            "quality_regeneration",
            f"Лучший вариант ниже порога {min_quality}, пробую заново",
            {"attempt": attempt, "best_score": best["quality"]["score"], "topic": topic},
        )

    if last_best is None:
        raise RuntimeError("Не удалось собрать ни одного варианта поста.")
    if require_minimum_quality and last_best["quality"]["score"] < min_quality:
        record_skip(
            "quality_below_threshold",
            f"Лучший вариант {last_best['quality']['score']} ниже порога {min_quality}",
            {"topic": topic, "source": signal.get("source_name"), "url": signal.get("url")},
        )
        raise RuntimeError(f"Лучший вариант набрал только {last_best['quality']['score']} из {min_quality}.")

    package = {
        "id": uuid4().hex,
        "created_at": datetime.now().isoformat(),
        "slot": slot,
        "signal": signal,
        "topic": topic,
        "plan": plan,
        "cta": select_cta(plan, bundle),
        "variants": last_variants,
        "best_variant": last_best,
        "media": choose_media(plan, signal, allow_media),
        "pool_size": len(pool),
    }
    record_selection(
        {
            "package_id": package["id"],
            "topic": topic,
            "slot": slot,
            "source": signal.get("source_name"),
            "title": signal.get("title"),
            "score": selected["score"],
            "pool_size": len(pool),
            "best_variant_score": last_best["quality"]["score"],
        }
    )
    return package
