from __future__ import annotations
from typing import Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .state_store import load_state, save_state, remember_publication, record_skip
from .newsroom import create_package
from .publisher import publish_to_channel

async def autopost_job(application:Any, slot:str)->None:
    st=load_state()
    if not st.get('autopost_enabled'): return
    bundle=application.bot_data['bundle']; channel=application.bot_data.get('channel_id','')
    if not channel: record_skip('no_channel_id','Не задан TELEGRAM_CHANNEL_ID'); return
    try:
        package=create_package(bundle, forced_slot=slot); variant=package['best_variant']; used=await publish_to_channel(application.bot,channel,variant,package['media'],package.get('topic')); remember_publication(package,variant,'autopost',used)
    except Exception as exc: record_skip('autopost_failed',str(exc),{'slot':slot})

def build_scheduler(application:Any)->AsyncIOScheduler:
    old=application.bot_data.get('scheduler')
    if old:
        try: old.shutdown(wait=False)
        except Exception: pass
    bundle=application.bot_data['bundle']; sched=AsyncIOScheduler(timezone=bundle.policy.get('timezone','Europe/Moscow'))
    times=load_state().get('post_times') or bundle.policy.get('default_post_times',['09:00','14:00','19:00']); slots=['morning','day','evening']
    for i,t in enumerate(times):
        try: h,m=[int(x) for x in t.split(':')]
        except Exception: continue
        sched.add_job(autopost_job, CronTrigger(hour=h, minute=m), args=[application, slots[i] if i<3 else 'day'], id=f'autopost_{i}', replace_existing=True)
    sched.start(); application.bot_data['scheduler']=sched; return sched

def set_autopost(enabled:bool)->None:
    st=load_state(); st['autopost_enabled']=enabled; save_state(st)

def set_schedule(times:list[str])->None:
    st=load_state(); st['post_times']=times; save_state(st)
