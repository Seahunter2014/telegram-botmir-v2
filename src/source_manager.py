from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin
import re, requests
from bs4 import BeautifulSoup
from .signal_extractor import clean_text, make_signal
from .state_store import load_state, save_state, record_skip
HEADERS={'User-Agent':'Mozilla/5.0 MirNaLadoniNewsroomBot/1.0'}


def fetch(url: str) -> str:
    r=requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status(); r.encoding=r.encoding or 'utf-8'; return r.text


def _telegram_photo(msg) -> str:
    node=msg.select_one('a.tgme_widget_message_photo_wrap')
    if not node: return ''
    style=node.get('style','')
    m=re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
    return m.group(1) if m else ''


def parse_telegram(source: dict[str, Any], html: str) -> list[dict[str, Any]]:
    soup=BeautifulSoup(html,'lxml'); out=[]
    for msg in soup.select('.tgme_widget_message')[-15:]:
        node=msg.select_one('.tgme_widget_message_text')
        if not node: continue
        text=clean_text(node.get_text(' ', strip=True))
        if len(text)<40: continue
        a=msg.select_one('a.tgme_widget_message_date'); url=a.get('href') if a else source['endpoint']
        t=msg.select_one('time'); dt=t.get('datetime') if t else ''
        title=text.split('. ')[0][:140]
        out.append(make_signal(source, title, url, text, dt, media_url=_telegram_photo(msg)))
    return out


def parse_site(source: dict[str, Any], html: str) -> list[dict[str, Any]]:
    soup=BeautifulSoup(html,'lxml'); out=[]
    for a in soup.find_all('a')[:120]:
        title=clean_text(a.get_text(' ', strip=True)); href=a.get('href') or ''
        if len(title)<20 or not href: continue
        out.append(make_signal(source, title, urljoin(source['endpoint'], href), title, ''))
        if len(out)>=15: break
    if not out:
        title=clean_text(soup.title.get_text(' ', strip=True) if soup.title else source['name']); out.append(make_signal(source,title,source['endpoint'],title,''))
    return out


def collect_from_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    html=fetch(source['endpoint']); method=source.get('collection_method')
    if method=='telegram_public_html': return parse_telegram(source, html)
    return parse_site(source, html)


def enabled_sources(bundle: Any) -> list[dict[str, Any]]:
    return [s for s in bundle.sources['sources'] if s.get('enabled') and s.get('mode')=='auto']


def collect_signals(bundle: Any, max_sources: int=7) -> list[dict[str, Any]]:
    sources=enabled_sources(bundle); state=load_state(); cursor=int(state.get('source_cursor',0))%max(1,len(sources)); ordered=sources[cursor:]+sources[:cursor]
    all_items=[]; errors=[]
    for src in ordered[:max_sources]:
        try: all_items.extend(collect_from_source(src))
        except Exception as exc: errors.append(f"{src['key']}: {exc}")
    state['source_cursor']=(cursor+max_sources)%max(1,len(sources)); save_state(state)
    if not all_items: record_skip('source_collection_failed','; '.join(errors[:5]), {'errors':errors})
    return all_items


def freshness_score(signal: dict[str, Any]) -> int:
    v=signal.get('published_at') or signal.get('collected_at')
    try:
        dt=datetime.fromisoformat(v.replace('Z','+00:00')).astimezone(timezone.utc); hours=(datetime.now(timezone.utc)-dt).total_seconds()/3600
        return 20 if hours<=24 else 15 if hours<=72 else 10 if hours<=168 else 3
    except Exception: return 10
