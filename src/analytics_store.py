from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
from .config_loader import ROOT_DIR
PATH=ROOT_DIR/'data'/'analytics.json'
def record_event(event_type:str, payload:dict[str,Any])->None:
    try: data=json.loads(PATH.read_text(encoding='utf-8'))
    except Exception: data={'posts':[]}
    data.setdefault('posts',[]).append({'time':datetime.now(timezone.utc).isoformat(),'event_type':event_type,'payload':payload})
    PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
