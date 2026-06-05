from __future__ import annotations
import logging, os
from functools import wraps
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
from src import BOT_VERSION
from src.config_loader import load_config
from src.newsroom import create_package
from src.publisher import publish_to_channel, render_post
from telegram.constants import ParseMode
from src.state_store import load_state, remember_publication, record_skip, append_rejected, load_publication_log
from src.scheduler import build_scheduler, set_autopost, set_schedule
from src.ai_writer import rewrite_variant
from src.quality_selector import score_variant, select_best_variant

if load_dotenv: load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger=logging.getLogger('mir_na_ladoni.newsroom')
TOKEN=os.getenv('TELEGRAM_BOT_TOKEN','').strip()
ADMIN=os.getenv('TELEGRAM_ADMIN_ID','').strip()
CHANNEL=os.getenv('TELEGRAM_CHANNEL_ID','').strip()
TEST_CHANNEL=os.getenv('TEST_CHANNEL_ID','').strip()

def admin_id()->int|None:
    try: return int(ADMIN) if ADMIN else None
    except ValueError: return None

async def reply(update:Update, text:str, markup:InlineKeyboardMarkup|None=None, html:bool=False)->None:
    kwargs={'reply_markup': markup, 'disable_web_page_preview': True}
    if html:
        kwargs['parse_mode'] = ParseMode.HTML
    if update.message:
        await update.message.reply_text(text[:3900], **kwargs)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text[:3900], **kwargs)

def admin_only(func):
    @wraps(func)
    async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE):
        aid=admin_id()
        if aid is None:
            await reply(update,'Не задан TELEGRAM_ADMIN_ID в Railway Variables.'); return
        if not update.effective_user or update.effective_user.id != aid:
            await reply(update,'Доступ только для администратора.'); return
        return await func(update, context)
    return wrapper

def bundle(context:ContextTypes.DEFAULT_TYPE): return context.application.bot_data['bundle']
def channel_id(context:ContextTypes.DEFAULT_TYPE)->str: return os.getenv('TELEGRAM_CHANNEL_ID', CHANNEL).strip()
def test_channel_id(context:ContextTypes.DEFAULT_TYPE)->str: return os.getenv('TEST_CHANNEL_ID', TEST_CHANNEL).strip() or channel_id(context)
def drafts(context:ContextTypes.DEFAULT_TYPE)->dict[str,Any]: return context.application.bot_data.setdefault('drafts',{})

def variant_keyboard(package:dict)->InlineKeyboardMarkup:
    pid=package['id']
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Опубликовать 1', callback_data=f'publish:{pid}:0'), InlineKeyboardButton('✅ Опубликовать 2', callback_data=f'publish:{pid}:1'), InlineKeyboardButton('✅ Опубликовать 3', callback_data=f'publish:{pid}:2')],
        [InlineKeyboardButton('🔁 Переписать', callback_data=f'rewrite:{pid}:best'), InlineKeyboardButton('🌿 Мягче', callback_data=f'softer:{pid}:best'), InlineKeyboardButton('🔥 Продающе', callback_data=f'sales:{pid}:best')],
        [InlineKeyboardButton('❌ Отклонить тему', callback_data=f'reject:{pid}:0')]
    ])

def summary(package:dict)->str:
    p=package['plan']; s=package['signal']; c=package.get('cta',{})
    return f"Пакет: {package['id']}\nИсточник: {s.get('source_name')}\nСсылка: {s.get('url')}\nЖанр: {p.get('topic')} / {p.get('genre')}\nСлот: {p.get('slot_ru')}\nScore темы: {p.get('score',{}).get('score')}\nПочему выбрано: {p.get('hook_angle')}\nCTA: {c.get('format')}\nКнопок: {len(c.get('buttons',[]))}"

async def send_preview(update:Update, context:ContextTypes.DEFAULT_TYPE, package:dict)->None:
    drafts(context)[package['id']]=package
    await reply(update, summary(package))
    for i,v in enumerate(package['variants'],1):
        q=v.get('quality',{})
        await reply(update, f"ВАРИАНТ {i}\nОценка: {q.get('score')}\nСтиль: {v.get('style')}\n\n{render_post(v, package['topic'])}", html=True)
    await reply(update,'Выберите действие:', variant_keyboard(package))

@admin_only
async def start_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    await reply(update,'AI-редакция «Мир на ладони» готова.\n\n/test — 3 варианта\n/preview — предпросмотр\n/publish — опубликовать лучший текущий вариант в тестовый канал\n/autopost_on /autopost_off — автопостинг\n/schedule 09:00,14:00,19:00 — расписание\n/status — статус\n/last — последняя публикация\n/why_skipped — последний пропуск\n/sources /topics /services — реестры\n/version — версия')

@admin_only
async def version_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    b=bundle(context); st=load_state()
    await reply(update, f"mirnala_bot_v3 — {BOT_VERSION}\nПроект: {b.policy.get('project_name')}\nТем: {len(b.topics['topics'])}\nИсточников: {len(b.sources['sources'])}\nСервисов: {len(b.services['services'])}\nКанал: {channel_id(context) or 'не задан'}\nТестовый канал: {test_channel_id(context) or 'не задан'}\nАвтопостинг: {'вкл' if st.get('autopost_enabled') else 'выкл'}\nРасписание: {', '.join(st.get('post_times', b.policy.get('default_post_times', [])))}")

@admin_only
async def test_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    topic=context.args[0] if context.args else None
    try:
        package=create_package(bundle(context), forced_topic=topic, allow_media=True)
        await send_preview(update, context, package)
    except Exception as exc:
        record_skip('test_failed', str(exc)); await reply(update, f'Тест не собрался: {exc}')

@admin_only
async def preview_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    await test_cmd(update, context)

@admin_only
async def publish_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    if not drafts(context): await reply(update,'Нет готового пакета. Сначала выполните /test.'); return
    package=list(drafts(context).values())[-1]; variant=package.get('best_variant') or select_best_variant(package['variants'], package['plan'], bundle(context))
    target=test_channel_id(context)
    if not target: await reply(update,'Не задан TEST_CHANNEL_ID или TELEGRAM_CHANNEL_ID.'); return
    used=await publish_to_channel(context.bot,target,variant,package['media'],package.get('topic')); remember_publication(package,variant,'manual_publish',used); await reply(update,f'Опубликовано в {target}.')

@admin_only
async def autopost_on_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    set_autopost(True); build_scheduler(context.application); await reply(update,'Автопостинг включён.')
@admin_only
async def autopost_off_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    set_autopost(False); await reply(update,'Автопостинг выключен.')
@admin_only
async def schedule_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    if context.args:
        times=' '.join(context.args).replace(' ','').split(',')
        if len(times)!=3 or any(':' not in t for t in times): await reply(update,'Формат: /schedule 09:00,14:00,19:00'); return
        set_schedule(times); build_scheduler(context.application); await reply(update,'Расписание обновлено: '+', '.join(times)); return
    await reply(update,'Расписание: '+', '.join(load_state().get('post_times',[])))
@admin_only
async def status_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    st=load_state(); await reply(update, f"Автопостинг: {'вкл' if st.get('autopost_enabled') else 'выкл'}\nПоследний пропуск: {st.get('last_skip_report') or '—'}\nПоследний выбор: {st.get('last_selection_report') or '—'}")
@admin_only
async def last_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    log=load_publication_log(); await reply(update, str(log[-1])[:3900] if log else 'Публикаций пока нет.')
@admin_only
async def why_skipped_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    await reply(update, str(load_state().get('last_skip_report') or 'Пропусков пока нет.')[:3900])
@admin_only
async def sources_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    await reply(update, '\n'.join(['Источники:']+[f"- {s['name']} — {s['endpoint']}" for s in bundle(context).sources['sources']])[:3900])
@admin_only
async def topics_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    await reply(update, '\n'.join(['Темы:']+[f"- {t['key']} — {t['name']}" for t in bundle(context).topics['topics']])[:3900])
@admin_only
async def services_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    await reply(update, '\n'.join(['Сервисы:']+[f"- {s['name']} — {s['ref_url']}" for s in bundle(context).services['services']])[:3900])

async def callback_handler(update:Update, context:ContextTypes.DEFAULT_TYPE)->None:
    q=update.callback_query
    if not q: return
    await q.answer()
    if admin_id() is None or not q.from_user or q.from_user.id!=admin_id(): await q.message.reply_text('Доступ только для администратора.'); return
    parts=(q.data or '').split(':')
    if len(parts)<3: return
    action,pid,value=parts[0],parts[1],parts[2]; package=drafts(context).get(pid)
    if not package: await q.message.reply_text('Пакет не найден. Выполните /test заново.'); return
    if action=='publish':
        idx=int(value); variant=package['variants'][idx]; target=channel_id(context) or test_channel_id(context)
        used=await publish_to_channel(context.bot,target,variant,package['media'],package.get('topic')); remember_publication(package,variant,'manual_approved',used); await q.message.reply_text(f'Опубликован вариант {idx+1} в {target}.'); return
    if action in {'rewrite','softer','sales'}:
        try:
            base=package.get('best_variant') or package['variants'][0]; new=rewrite_variant(base, package['plan'], package['signal'], bundle(context), action); new['quality']=score_variant(new,package['plan'],bundle(context)); package['variants']=[new]+package['variants'][:2]; package['best_variant']=new; drafts(context)[pid]=package; await q.message.reply_text('Новый вариант:\n\n'+render_post(new, package['topic'])[:3600], reply_markup=variant_keyboard(package), parse_mode=ParseMode.HTML)
        except Exception as exc: await q.message.reply_text(f'Не удалось переписать: {exc}')
        return
    if action=='reject': append_rejected({'package':pid,'signal':package.get('signal'),'plan':package.get('plan')}); drafts(context).pop(pid,None); await q.message.reply_text('Тема отклонена. Можно выполнить /test заново.'); return

async def post_init(application:Application)->None:
    b=load_config(); application.bot_data['bundle']=b; application.bot_data['channel_id']=CHANNEL; application.bot_data['test_channel_id']=TEST_CHANNEL; build_scheduler(application)

def build_application()->Application:
    if not TOKEN: raise RuntimeError('TELEGRAM_BOT_TOKEN не задан')
    app=Application.builder().token(TOKEN).post_init(post_init).build()
    for name,func in [('start',start_cmd),('version',version_cmd),('test',test_cmd),('preview',preview_cmd),('publish',publish_cmd),('autopost_on',autopost_on_cmd),('autopost_off',autopost_off_cmd),('schedule',schedule_cmd),('status',status_cmd),('last',last_cmd),('why_skipped',why_skipped_cmd),('sources',sources_cmd),('topics',topics_cmd),('services',services_cmd)]: app.add_handler(CommandHandler(name,func))
    app.add_handler(CallbackQueryHandler(callback_handler)); return app

def main()->None:
    logger.info('BOOT VERSION: %s', BOT_VERSION); build_application().run_polling(drop_pending_updates=True)
if __name__=='__main__': main()
