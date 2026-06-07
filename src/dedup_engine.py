from __future__ import annotations
from difflib import SequenceMatcher
from hashlib import sha256
from .state_store import load_state, fingerprint

def norm(s:str)->str: return ' '.join(''.join(ch.lower() if ch.isalnum() or ch.isspace() else ' ' for ch in s).split())

def is_duplicate_signal(signal: dict) -> tuple[bool,str]:
    st=load_state(); url=signal.get('url',''); title=signal.get('title',''); fp=fingerprint(title+'\n'+signal.get('text',''))
    if url and url in st.get('published_urls',[]): return True,'URL уже публиковался'
    nt=norm(title)
    for old in st.get('published_titles',[])[-200:]:
        if SequenceMatcher(None,nt,norm(old)).ratio()>=0.82: return True,'Похожий заголовок уже был'
    for old in st.get('published_semantic_fingerprints',[])[-200:]:
        if SequenceMatcher(None,fp,old).ratio()>=0.78: return True,'Смысловой повтор'
    return False,''

def is_duplicate_variant(text:str)->tuple[bool,str]:
    st=load_state(); h=sha256(text.encode()).hexdigest(); fp=fingerprint(text)
    if h in st.get('published_text_hashes',[]): return True,'Точный текст уже публиковался'
    for old in st.get('published_semantic_fingerprints',[])[-200:]:
        if SequenceMatcher(None,fp,old).ratio()>=0.78: return True,'Текст слишком похож на прошлую публикацию'
    return False,''

def rotation_penalty(signal:dict, topic:str)->tuple[int,list[str]]:
    st=load_state(); p=0; r=[]
    if topic in st.get('published_topics',[])[-2:]: p+=20; r.append('жанр недавно был')
    if signal.get('source_key') in st.get('published_sources',[])[-2:]: p+=10; r.append('источник недавно был')
    if signal.get('country') and signal.get('country') in st.get('published_countries',[])[-3:]: p+=12; r.append('страна недавно была')
    if topic in {'visa_or_residence','relocation'} and any(x in {'visa_or_residence','relocation'} for x in st.get('published_topics',[])[-1:]): p+=25; r.append('визовые темы не подряд')
    return p,r
