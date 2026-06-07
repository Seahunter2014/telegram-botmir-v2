from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class ConfigBundle:
    topics: dict[str, Any]
    sources: dict[str, Any]
    services: dict[str, Any]
    link_rules: dict[str, Any]
    forbidden: dict[str, Any]
    policy: dict[str, Any]
    prompts: dict[str, str]
    root_dir: Path

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def load_prompts(root: Path = ROOT_DIR) -> dict[str, str]:
    return {p.stem: p.read_text(encoding='utf-8') for p in sorted((root/'prompts').glob('*.md'))}

def load_config(root: Path = ROOT_DIR) -> ConfigBundle:
    cfg = root/'configs'
    bundle = ConfigBundle(
        topics=load_json(cfg/'topics.json'),
        sources=load_json(cfg/'sources.json'),
        services=load_json(cfg/'services.json'),
        link_rules=load_json(cfg/'link_rules.json'),
        forbidden=load_json(cfg/'forbidden_phrases.json'),
        policy=load_json(cfg/'editorial_policy.json'),
        prompts=load_prompts(root),
        root_dir=root,
    )
    if not bundle.topics.get('topics') or not bundle.sources.get('sources') or not bundle.services.get('services'):
        raise RuntimeError('Конфиги тем, источников или сервисов пустые')
    if 'system_editor_ru' not in bundle.prompts:
        raise RuntimeError('Не найден prompts/system_editor_ru.md')
    return bundle

def link_rule_for_topic(bundle: ConfigBundle, topic: str) -> dict[str, Any] | None:
    return next((r for r in bundle.link_rules['rules'] if r.get('topic') == topic), None)
