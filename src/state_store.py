from __future__ import annotations
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from .config_loader import ROOT_DIR

STATE_PATH = ROOT_DIR/'data'/'state.json'
LOG_PATH = ROOT_DIR/'data'/'publication_log.json'
REJECT_PATH = ROOT_DIR/'data'/'rejected_topics.json'

def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding='utf-8')
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        path.rename(path.with_suffix(path.suffix+'.broken'))
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding='utf-8')
        return default

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)

def load_state() -> dict[str, Any]: return read_json(STATE_PATH, {})
def save_state(state: dict[str, Any]) -> None: write_json(STATE_PATH, state)
def load_publication_log() -> list[dict[str, Any]]: return read_json(LOG_PATH, [])

def fingerprint(text: str) -> str:
    cleaned = ''.join(ch.lower() if ch.isalnum() or ch.isspace() else ' ' for ch in text)
    words = [w for w in cleaned.split() if len(w) > 3]
    return ' '.join(words[:80])

def record_skip(reason: str, details: str = '', extra: dict[str, Any] | None = None) -> None:
    state = load_state(); state['last_skip_report']={'time':datetime.now(timezone.utc).isoformat(),'reason':reason,'details':details, **(extra or {})}; save_state(state)

def record_selection(report: dict[str, Any]) -> None:
    state = load_state(); state['last_selection_report']={'time':datetime.now(timezone.utc).isoformat(), **report}; save_state(state)

def remember_publication(package: dict[str, Any], variant: dict[str, Any], mode: str, used_media: bool) -> None:
    state=load_state(); signal=package['signal']; plan=package['plan']; text=(variant.get('title','')+'\n'+variant.get('text','')).strip()
    for key in ['published_urls','published_titles','published_text_hashes','published_semantic_fingerprints','published_topics','published_genres','published_countries','published_cities','published_sources']:
        state.setdefault(key, [])
    state['published_urls'].append(signal.get('url','')); state['published_titles'].append(signal.get('title',''))
    state['published_text_hashes'].append(sha256(text.encode()).hexdigest()); state['published_semantic_fingerprints'].append(fingerprint(text))
    state['published_topics'].append(plan.get('topic','')); state['published_genres'].append(plan.get('genre',''))
    state['published_countries'].append(plan.get('country','')); state['published_cities'].append(plan.get('city','')); state['published_sources'].append(signal.get('source_key',''))
    for key in list(state):
        if key.startswith('published_'): state[key] = [x for x in state[key] if x][-200:]
    save_state(state)
    log=load_publication_log(); log.append({'time':datetime.now(timezone.utc).isoformat(),'mode':mode,'used_media':used_media,'source':signal,'plan':plan,'variant':{'title':variant.get('title'),'score':variant.get('quality',{}).get('score')}}); write_json(LOG_PATH, log[-1000:])

def append_rejected(record: dict[str, Any]) -> None:
    data=read_json(REJECT_PATH, []); data.append({'time':datetime.now(timezone.utc).isoformat(), **record}); write_json(REJECT_PATH, data[-1000:])
