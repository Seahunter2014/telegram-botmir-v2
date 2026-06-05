from __future__ import annotations
from datetime import datetime
from typing import Any
from .topic_classifier import infer_slot_by_hour

def current_slot(bundle_policy:dict, forced:str|None=None)->str:
    return forced if forced in {'morning','day','evening'} else infer_slot_by_hour(datetime.now().hour)

def slot_name_ru(slot:str)->str:
    return {'morning':'утренний','day':'дневной','evening':'вечерний'}.get(slot,slot)
