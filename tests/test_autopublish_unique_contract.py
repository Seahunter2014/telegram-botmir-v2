from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

scheduler = (ROOT / 'src' / 'scheduler.py').read_text(encoding='utf-8')
pipeline = (ROOT / 'src' / 'pipeline.py').read_text(encoding='utf-8')
dedup = (ROOT / 'src' / 'dedup_engine.py').read_text(encoding='utf-8')
ai_writer = (ROOT / 'src' / 'ai_writer.py').read_text(encoding='utf-8')

assert 'asyncio.create_task' not in scheduler, 'scheduler must not use create_task inside APScheduler job wrapper'
assert 'misfire_grace_time=1800' in scheduler, 'autopost jobs must tolerate delayed execution'
assert 'single_rewrite_below_80' in pipeline, 'pipeline must do exactly one rewrite below 80'
assert 'for attempt in range(1, 9)' not in pipeline, 'pipeline must not run 8 rewrite attempts'
assert 'remember_topic_attempt' in pipeline, 'pipeline must remember every attempted topic'
assert 'topic_memory' in dedup and 'rejected_topics' in dedup, 'dedup must check published, preview, attempted and rejected topics'
assert 'ПАМЯТЬ ОЦЕНОК АДМИНИСТРАТОРА' in ai_writer, 'AI prompt must include admin rating memory'
print('OK: autopublish unique contract')
