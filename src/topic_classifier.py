from __future__ import annotations
from typing import Any
RULES={'flight_deal':['билет','авиабилет','перелёт','рейс','туда-обратно'],'tour_offer':['тур','путёвка','пакет','all inclusive'],'hotel_post':['отель','гостиница','проживание'],'event_trip':['событие','фестиваль','выставка'],'concert_trip':['концерт','артист','звезда'],'visa_or_residence':['виза','внж','гражданство','правила въезда'],'relocation':['релокация','переезд','экспат'],'payment_abroad':['карта','swift','оплата за границей'],'insurance_tip':['страховка','полис'],'rail_trip':['поезд','жд'],'road_trip':['аренда авто','машина','авто'],'beach_trip':['море','пляж','остров','курорт'],'mountain_trip':['горы','каньон','озеро']}

def classify_signal(signal: dict[str, Any], bundle: Any, slot: str='day') -> str:
    text=f"{signal.get('title','')} {signal.get('text','')} {signal.get('raw_role','')}".lower(); sk=signal.get('source_key','')
    if sk=='travelata_telegram': return 'tour_offer'
    if sk in {'gorbilet_events','psgr_concerts'}: return 'concert_trip' if 'концерт' in text else 'event_trip'
    if sk in {'imigrata','relocate_easy','ekspat_info'}: return 'payment_abroad' if any(w in text for w in ['карта','swift','оплата']) else 'visa_or_residence'
    if sk=='trip_activities': return 'weekend_activity'
    for topic, words in RULES.items():
        if any(w in text for w in words): return topic
    return 'destination_post' if slot=='morning' else 'practical_travel' if slot=='evening' else 'weekend_trip'

def infer_slot_by_hour(hour:int)->str:
    return 'morning' if hour<12 else 'day' if hour<17 else 'evening'
