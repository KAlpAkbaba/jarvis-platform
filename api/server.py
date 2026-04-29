import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import httpx
import tempfile
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import config

app = FastAPI(title="Jarvis Platform", version="1.0.0")

try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = []

@app.get("/")
async def root():
    try:
        with open("frontend/static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except:
        return HTMLResponse("<h1>Jarvis Platform</h1>")

@app.get("/health")
async def health():
    return {"status": "ok", "model": config.llm_model}


async def generate_session_title(session_id: str, first_user_msg: str, first_assistant_msg: str):
    """İlk mesajdan kısa konu başlığı üretir ve DB'ye kaydeder."""
    try:
        import httpx as _hx, json as _js
        prompt = f"Kullanici mesaji: {first_user_msg}\nAsistan cevabi: {first_assistant_msg[:200]}\nBu sohbetin konusunu 4-6 kelimeyle ozetle. Sadece ozet yaz, baska hicbir sey yazma."
        async with _hx.AsyncClient(timeout=15) as cl:
            r = await cl.post("http://172.17.0.1:11434/api/chat", json={
                "model": "qwen2.5:7b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            })
            title = r.json().get("message", {}).get("content", "").strip()[:60]
            if title:
                from database.db import SessionLocal as _SL2
                from sqlalchemy import text as _t2
                _db2 = _SL2()
                _db2.execute(_t2(
                    "INSERT INTO session_titles (session_id, title) VALUES (:s, :t) ON CONFLICT (session_id) DO UPDATE SET title = :t"
                ), {"s": session_id, "t": title})
                _db2.commit()
                _db2.close()
    except Exception as _e:
        print(f"Session title error: {_e}")

def load_session_history(session_id: str, limit: int = 12):
    """Session'ın DB geçmişini yükler."""
    try:
        from database.db import SessionLocal as _SL3
        from sqlalchemy import text as _t3
        _db3 = _SL3()
        rows = _db3.execute(_t3(
            "SELECT role, content FROM sohbet_gecmisi WHERE session_id = :s ORDER BY created_at DESC LIMIT :l"
        ), {"s": session_id, "l": limit}).fetchall()
        _db3.close()
        history = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
        return history
    except:
        return []

def extract_topic(history: list) -> str:
    """Son konuşmadan ana konuyu/nesneyi çıkarır."""
    for msg in reversed(history):
        if msg["role"] == "user":
            content = msg["content"].strip()
            # 10 kelimeden uzun mesajlarda konu var demektir
            if len(content.split()) >= 3:
                return content
    return ""

def resolve_context(text: str, history: list) -> str:
    """Kisa/belirsiz mesajlara onceki konuyu ekler — sadece aynı konu devam ediyorsa."""
    words = text.strip().split()

    # Yeni bir nesne/konu adı varsa context ekleme
    # 3+ kelimeli sorular genellikle kendi başına tamamdır
    if len(words) >= 3:
        return text

    short_question_starters = ["nerede", "ne zaman", "nasil", "neden", "ne kadar",
                                "kac", "neye", "neyle", "nereye", "nereden",
                                "kim tarafindan", "hangi ulkede", "kac yilinda"]
    has_pronoun = any(w in text.lower() for w in ["onu", "onun", "bunun", "bunu", "orada", "orasi"])
    starts_with_question = any(text.lower().startswith(s) for s in short_question_starters)

    # Sadece zamir veya çok kısa soru starter varsa context ekle
    if has_pronoun or (len(words) <= 2 and starts_with_question):
        topic = extract_topic(history[:-1] if history else [])
        if topic and topic.lower() not in text.lower():
            topic_words = topic.split()[:3]
            topic_short = " ".join(topic_words)
            return f"{topic_short} - {text}"
    return text


async def generate_session_title(session_id: str, first_user_msg: str, first_assistant_msg: str):
    """İlk mesajdan kısa konu başlığı üretir ve DB'ye kaydeder."""
    try:
        import httpx as _hx, json as _js
        prompt = f"Kullanici mesaji: {first_user_msg}\nAsistan cevabi: {first_assistant_msg[:200]}\nBu sohbetin konusunu 4-6 kelimeyle ozetle. Sadece ozet yaz, baska hicbir sey yazma."
        async with _hx.AsyncClient(timeout=15) as cl:
            r = await cl.post("http://172.17.0.1:11434/api/chat", json={
                "model": "qwen2.5:7b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            })
            title = r.json().get("message", {}).get("content", "").strip()[:60]
            if title:
                from database.db import SessionLocal as _SL2
                from sqlalchemy import text as _t2
                _db2 = _SL2()
                _db2.execute(_t2(
                    "INSERT INTO session_titles (session_id, title) VALUES (:s, :t) ON CONFLICT (session_id) DO UPDATE SET title = :t"
                ), {"s": session_id, "t": title})
                _db2.commit()
                _db2.close()
    except Exception as _e:
        print(f"Session title error: {_e}")

def load_session_history(session_id: str, limit: int = 12):
    """Session'ın DB geçmişini yükler."""
    try:
        from database.db import SessionLocal as _SL3
        from sqlalchemy import text as _t3
        _db3 = _SL3()
        rows = _db3.execute(_t3(
            "SELECT role, content FROM sohbet_gecmisi WHERE session_id = :s ORDER BY created_at DESC LIMIT :l"
        ), {"s": session_id, "l": limit}).fetchall()
        _db3.close()
        history = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
        return history
    except:
        return []

def extract_topic(history: list) -> str:
    """Son konuşmadan ana konuyu/nesneyi çıkarır."""
    for msg in reversed(history):
        if msg["role"] == "user":
            content = msg["content"].strip()
            # 10 kelimeden uzun mesajlarda konu var demektir
            if len(content.split()) >= 3:
                return content
    return ""

def resolve_context(text: str, history: list) -> str:
    """Kisa/belirsiz mesajlara onceki konuyu ekler — sadece aynı konu devam ediyorsa."""
    words = text.strip().split()

    # Yeni bir nesne/konu adı varsa context ekleme
    # 3+ kelimeli sorular genellikle kendi başına tamamdır
    if len(words) >= 3:
        return text

    short_question_starters = ["nerede", "ne zaman", "nasil", "neden", "ne kadar",
                                "kac", "neye", "neyle", "nereye", "nereden",
                                "kim tarafindan", "hangi ulkede", "kac yilinda"]
    has_pronoun = any(w in text.lower() for w in ["onu", "onun", "bunun", "bunu", "orada", "orasi"])
    starts_with_question = any(text.lower().startswith(s) for s in short_question_starters)

    # Sadece zamir veya çok kısa soru starter varsa context ekle
    if has_pronoun or (len(words) <= 2 and starts_with_question):
        topic = extract_topic(history[:-1] if history else [])
        if topic and topic.lower() not in text.lower():
            topic_words = topic.split()[:3]
            topic_short = " ".join(topic_words)
            return f"{topic_short} - {text}"
    return text

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        from core.assistant import Assistant
        from core.router import normalize
        assistant = Assistant()
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            text = payload.get("text", "")
            session_id = payload.get("session_id", "default")
            chat_mode  = payload.get("mode", "hizli")  # "hizli" veya "arastirma"
            if not text:
                continue
            # Kullanici mesajini kaydet
            user_id = payload.get("user_id")
            # Session geçmişini yükle
            session_history = load_session_history(session_id)
            # Konu takibi — kısa/belirsiz sorulara önceki konuyu ekle
            # Kimlik sorularinda context resolution yapma
            _kimlik_check = ["sen kimsin", "kim yaratti", "amacin ne", "ne yapabilirsin", "kim gelistirdi"]
            if any(k in text.lower() for k in _kimlik_check):
                resolved_text = text
            else:
                resolved_text = resolve_context(text, session_history)
            _history.save_message(session_id, "user", text, user_id)
            # İlk mesaj mı? Başlık üretimi için bayrak
            is_first_msg = len([m for m in session_history if m["role"] == "user"]) == 0

            # Kimlik sorulari — dogrudan cevapla, LLM/web aramasina gitme
            _kimlik_map = {
                "seni kim yaratt": "Ben Jarvis, Aktivra tarafindan gelistirildim. Turkce konusan bir yapay zeka asistaniyim.",
                "seni kim gelistir": "Beni Aktivra gelistirdi. Turkce konusan bir yapay zeka asistaniyim.",
                "kim gelistirdi": "Beni Aktivra gelistirdi.",
                "kim gelistir": "Beni Aktivra gelistirdi.",
                "kim yaratti": "Beni Aktivra gelistirdi. Turkce konusan bir yapay zeka asistaniyim.",
                "sen kimsin": "Ben Jarvis! Aktivra tarafindan gelistirilmis bir yapay zeka asistaniyim. Web arama, takvim, not alma ve daha fazlasinda yardimci olabilirim.",
                "jarvis kimsin": "Ben Jarvis! Aktivra tarafindan gelistirilmis bir yapay zeka asistaniyim.",
                "amacin ne": "Amacim size Turkce olarak yardimci olmak — sorularinizi yanitlamak, takviminizi yonetmek ve gunluk islerinizi kolaylastirmak.",
                "ne yapabilirsin": "Web arama, hava durumu, takvim yonetimi, not alma ve hatirlatici kurabilir, genel sohbet yapabilirim!",
                "kim gelistirdi": "Beni Aktivra gelistirdi.",
                "kim olusturdu": "Beni Aktivra olusturdu.",
                "kim yapti": "Beni Aktivra yapti.",
                "gelistiren": "Beni Aktivra gelistirdi.",
                "kim tarafindan": "Aktivra tarafindan gelistirildim.",
                "tarafindan gelistir": "Aktivra tarafindan gelistirildim.",
                "nasil olusturuldun": "Aktivra ekibi tarafindan gelistirildim.",
                "nasil yapildin": "Aktivra muhendisleri tarafindan yapay zeka teknolojileriyle olusturuldum.",
            }
            # Turkce karakterleri normalize et
            def _normalize_tr(s):
                return s.lower().replace('ş','s').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ı','i').replace('ç','c').replace('Ş','s').replace('Ğ','g').replace('Ü','u').replace('Ö','o').replace('İ','i').replace('Ç','c')
            _text_lower = _normalize_tr(text.strip())
            _kimlik_yanit = None
            for k, v in _kimlik_map.items():
                if k in _text_lower:
                    _kimlik_yanit = v
                    break
            # Pending takvim etkinliği kontrolü
            _provider_keywords = {"google": "google", "gmail": "google", "outlook": "microsoft", "microsoft": "microsoft"}
            _text_lower_full = text.lower().strip()
            if user_id and any(k in _text_lower_full for k in ["google", "outlook", "microsoft", "her ikisi", "ikisi", "her iki"]):
                try:
                    from database.db import SessionLocal as _SL7
                    from sqlalchemy import text as _t7
                    import json as _js7
                    _db7 = _SL7()
                    _prow = _db7.execute(_t7("SELECT content FROM sohbet_gecmisi WHERE session_id = :s AND role = 'pending_event' ORDER BY created_at DESC LIMIT 1"), {"s": session_id}).fetchone()
                    if _prow:
                        _ev_pending = _js7.loads(_prow[0])
                        _ev_pending['user_id'] = user_id
                        # pending_event'i sil
                        _db7.execute(_t7("DELETE FROM sohbet_gecmisi WHERE session_id = :s AND role = 'pending_event'"), {"s": session_id})
                        _db7.commit()
                        _db7.close()
                        # Hangi provider?
                        _target_providers = []
                        if "her ikisi" in _text_lower_full or "ikisi" in _text_lower_full:
                            _target_providers = ["google", "microsoft"]
                        elif "google" in _text_lower_full or "gmail" in _text_lower_full:
                            _target_providers = ["google"]
                        elif "outlook" in _text_lower_full or "microsoft" in _text_lower_full:
                            _target_providers = ["microsoft"]
                        if _target_providers:
                            _results = []
                            async with httpx.AsyncClient(timeout=15) as _pc7:
                                for _prov7 in _target_providers:
                                    _ev_pending['provider'] = _prov7
                                    _r7 = await _pc7.post("http://172.17.0.1:8000/calendar/add/user", json=_ev_pending)
                                    _d7 = _r7.json()
                                    _plabel = "Google" if _prov7 == "google" else "Outlook"
                                    if _d7.get('status') == 'ok':
                                        _results.append(f"✓ {_plabel}")
                                    else:
                                        _results.append(f"✗ {_plabel}: {_d7.get('error','hata')}")
                            cal_response = f"**{_ev_pending.get('title')}** eklendi: {', '.join(_results)} — {_ev_pending.get('start','')[:16].replace('T',' ')}"
                            _history.save_message(session_id, "assistant", cal_response, user_id)
                            await websocket.send_text(json.dumps({"type": "response", "text": cal_response}))
                            continue
                    else:
                        _db7.close()
                except Exception as _pe7:
                    print(f"Pending event error: {_pe7}")

            # Kısa devam mesajları veya kişisel tercih — web aramasi yapma
            # Bilgi sorusu mu, devam mesajı mı?
            _bilgi_starter = ["nedir", "kimdir", "nasil", "neden", "ne zaman", "nerede", "anlat", "acikla", "hakkinda bilgi"]
            _kisa_bilgi_sorusu = len(text.strip().split()) <= 4 and any(k in _text_lower for k in _bilgi_starter)
            _kisisel_soru = (
                any(k in _text_lower for k in ["sen hangisini", "senin tercih", "sence hangisi", "peki sen", "sen ne dusunuyorsun", "ya sen", "sen tercih"])
                or (
                    len(text.strip().split()) <= 4  # Kısa mesaj
                    and len(session_history) > 2     # Aktif sohbet var
                    and not _kisa_bilgi_sorusu       # Bilgi sorusu değil
                )
            )
            if _kisisel_soru:
                # Direkt stream yap, web aramasi olmadan
                # Konuşma geçmişini mesaj listesi olarak hazırla
                _gecmis_mesajlar = [{"role": m["role"], "content": m["content"]} for m in session_history[-6:]]
                _kisisel_sistem = """Sen Jarvis'sin. Samimi, kisilikli ve konusmayi surdurebilen bir yapay zeka asistaniyim.
Kullanicinin kisa veya kisisel mesajlarina dogal bir konusma ortagi gibi yanit ver.
Nesnel bilgi verme, kisisel yorum yap. Kisa tut, cevabin sonunda konusmayi devam ettirecek bir soru sor."""
                _kisisel_prompt = text
                _kisisel_full = ""
                await websocket.send_text(json.dumps({"type": "stream_start"}))
                async with httpx.AsyncClient(timeout=30) as _kpc:
                    async with _kpc.stream("POST", "http://172.17.0.1:11434/api/chat", json={
                        "model": config.llm_model,
                        "messages": [{"role": "system", "content": _kisisel_sistem}] + _gecmis_mesajlar + [{"role": "user", "content": _kisisel_prompt}],
                        "stream": True
                    }) as _kpr:
                        async for _kline in _kpr.aiter_lines():
                            if _kline:
                                try:
                                    _kchunk = json.loads(_kline)
                                    _ktoken = _kchunk.get("message", {}).get("content", "")
                                    if _ktoken:
                                        _kisisel_full += _ktoken
                                        await websocket.send_text(json.dumps({"type": "stream", "text": _ktoken}))
                                except: pass
                await websocket.send_text(json.dumps({"type": "stream_end", "text": _kisisel_full}))
                _history.save_message(session_id, "assistant", _kisisel_full, user_id)
                continue

            if _kimlik_yanit:
                _history.save_message(session_id, "assistant", _kimlik_yanit, user_id)
                await websocket.send_text(json.dumps({"type": "stream_start"}))
                # Kelime kelime stream et
                import asyncio as _asyncio
                _words = _kimlik_yanit.split(" ")
                for _word in _words:
                    await websocket.send_text(json.dumps({"type": "stream", "text": _word + " "}))
                    await _asyncio.sleep(0.04)
                await websocket.send_text(json.dumps({"type": "stream_end", "text": _kimlik_yanit}))
                continue

            try:
                # Takvim kontrolu - WebSocket icin
                from core.router import normalize
                text_norm_ws = normalize(text.lower())
                takvim_goster_ws = ["takvim", "etkinlik", "randevu", "ajanda"]
                takvim_ekle_ws = ["takvime ekle", "etkinlik ekle", "randevu ekle", "toplanti ekle", "hatirlatici ekle", "ekle takvime", "takvime yaz", "toplantisi ekle", "toplanti ayarla", "randevu ayarla", "saat ekle", "toplanti kur"]
                hava_ws = ["hava", "sicaklik", "yagis", "derece"]
                tarih_ws = ["bugun", "saat kac", "tarih", "ayın kaci", "ayin kaci"]
                # Takvim ekleme: "ekle" + (tarih/saat/yarin/bugun) kombinasyonu da yakala
                _has_ekle = "ekle" in text_norm_ws
                _has_time = any(k in text_norm_ws for k in ["saat", "yarin", "bugun", "pazartesi", "sali", "carsamba", "persembe", "cuma", "cumartesi", "pazar", "hafta", "tarih"])
                _is_takvim_ekle = any(k in text_norm_ws for k in takvim_ekle_ws) or (_has_ekle and _has_time)
                if _is_takvim_ekle or any(k in text_norm_ws for k in takvim_goster_ws) or any(k in text_norm_ws for k in hava_ws) or any(k in text_norm_ws for k in tarih_ws):
                    if _is_takvim_ekle and user_id:
                        # LLM ile etkinlik bilgilerini parse et
                        from datetime import datetime as _dtnow2
                        _now_str = _dtnow2.now().strftime('%Y-%m-%d %H:%M')
                        from datetime import datetime as _dtnow3, timedelta as _td3
                        _bugun = _dtnow3.now().strftime('%Y-%m-%d')
                        _yarin = (_dtnow3.now() + _td3(days=1)).strftime('%Y-%m-%d')
                        _parse_prompt = f"""Bugun: {_now_str} ({_bugun})
Yarin: {_yarin}
Kullanici mesaji: "{text}"
Bu mesajdan takvim etkinligi bilgilerini cikart.
ONEMLI: "yarin" kelimesi geciyorsa tarihi {_yarin} olarak kullan, "bugun" veya tarih yoksa {_bugun} kullan.
SADECE asagidaki JSON formatinda don, baska hicbir sey yazma:
{{"title":"etkinlik adi","start":"{_yarin}T14:00:00","end":"{_yarin}T15:00:00"}}
Sure belirtilmemisse 1 saat ekle. Sadece JSON don."""
                        try:
                            async with httpx.AsyncClient(timeout=15) as _pc:
                                _pr = await _pc.post("http://172.17.0.1:11434/api/chat", json={"model": config.llm_model, "messages": [{"role":"user","content":_parse_prompt}], "stream": False})
                                import re as _re4
                                _raw_parse = _pr.json().get("message",{}).get("content","")
                                _jmatch = _re4.search(r'\{.*\}', _raw_parse, _re4.DOTALL)
                                if _jmatch:
                                    _ev_data = json.loads(_jmatch.group())
                                    _ev_data['user_id'] = user_id
                                    # Provider kontrolü
                                    from database.db import SessionLocal as _SL5
                                    from sqlalchemy import text as _t5
                                    _db5 = _SL5()
                                    _providers = [r[0] for r in _db5.execute(_t5("SELECT provider FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google','microsoft')"), {"u": user_id}).fetchall()]
                                    _db5.close()
                                    if not _providers:
                                        cal_response = "Takvim bağlı değil. Ayarlar > Takvim'den Google veya Microsoft takviminizi bağlayın."
                                    elif len(_providers) == 1:
                                        # Tek takvim — direkt ekle
                                        _ev_data['provider'] = _providers[0]
                                        _add_r = await _pc.post("http://172.17.0.1:8000/calendar/add/user", json=_ev_data)
                                        _add_d = _add_r.json()
                                        _prov_label = "Google" if _providers[0] == "google" else "Outlook"
                                        if _add_d.get('status') == 'ok':
                                            cal_response = f"✓ {_prov_label} takvimine eklendi: **{_ev_data.get('title')}** — {_ev_data.get('start','')[:16].replace('T',' ')}"
                                        else:
                                            cal_response = f"Etkinlik eklenemedi: {_add_d.get('error','Bilinmeyen hata')}"
                                    else:
                                        # Birden fazla takvim — kullanıcıya sor, pending olarak sakla
                                        import json as _js6
                                        _pending = _js6.dumps(_ev_data)
                                        from database.db import SessionLocal as _SL6
                                        from sqlalchemy import text as _t6
                                        _db6 = _SL6()
                                        _db6.execute(_t6("INSERT INTO sohbet_gecmisi (session_id, role, content, kullanici_id) VALUES (:s, 'pending_event', :c, :u)"), {"s": session_id, "c": _pending, "u": user_id})
                                        _db6.commit()
                                        _db6.close()
                                        cal_response = f"**{_ev_data.get('title')}** etkinliğini hangi takvime ekleyeyim?\n\n- **Google** takvim\n- **Outlook** takvim\n- **Her ikisi**"
                                else:
                                    cal_response = "Etkinlik bilgilerini anlayamadım. Örnek: 'Yarın saat 14:00'e toplantı ekle'"
                        except Exception as _pe:
                            cal_response = f"Etkinlik eklenirken hata: {str(_pe)}"
                        _history.save_message(session_id, "assistant", cal_response, user_id)
                        await websocket.send_text(json.dumps({"type": "response", "text": cal_response}))
                        continue
                    elif any(k in text_norm_ws for k in takvim_goster_ws) and user_id:
                        # Kullanici bazli takvim
                        from database.db import SessionLocal as _SL
                        from sqlalchemy import text as _text
                        from datetime import datetime as _dt, timedelta as _td
                        _db = _SL()
                        _rows = _db.execute(_text("SELECT provider, access_token, refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google','microsoft')"), {"u": user_id}).fetchall()
                        _db.close()
                        if _rows:
                            import requests as _req2
                            _lines = []
                            for _row in _rows:
                                _prov, _at, _rt = _row
                                if _prov == 'google':
                                    try:
                                        from google.oauth2.credentials import Credentials
                                        from googleapiclient.discovery import build
                                        import json as _js
                                        with open(GOOGLE_WEB_CREDS) as _f:
                                            _cfg = _js.load(_f)['web']
                                        _creds = Credentials(token=_at, refresh_token=_rt, token_uri='https://oauth2.googleapis.com/token', client_id=_cfg['client_id'], client_secret=_cfg['client_secret'])
                                        _svc = build('calendar', 'v3', credentials=_creds)
                                        _now = _dt.utcnow().isoformat() + 'Z'
                                        _end = (_dt.utcnow() + _td(days=7)).isoformat() + 'Z'
                                        _evts = _svc.events().list(calendarId='primary', timeMin=_now, timeMax=_end, maxResults=10, singleEvents=True, orderBy='startTime').execute().get('items', [])
                                        if _evts:
                                            _lines.append('Google takvimi:')
                                            for _e in _evts:
                                                _t = _e.get('summary','Basliksiz')
                                                _s = _e.get('start',{}).get('dateTime',_e.get('start',{}).get('date',''))
                                                try:
                                                    _edt = _dt.fromisoformat(_s.replace('Z','+00:00'))
                                                    _s = _edt.strftime('%d %B %Y %H:%M')
                                                except: pass
                                                _lines.append(f'- {_s} : {_t}')
                                    except Exception as _ge:
                                        _lines.append(f'Google takvim hatasi: {_ge}')
                                elif _prov == 'microsoft':
                                    try:
                                        _hdrs = {'Authorization': 'Bearer ' + _at}
                                        _now2 = _dt.utcnow().isoformat() + 'Z'
                                        _end2 = (_dt.utcnow() + _td(days=7)).isoformat() + 'Z'
                                        _r2 = _req2.get(f'https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={_now2}&endDateTime={_end2}&$top=10&$orderby=start/dateTime', headers=_hdrs)
                                        _me = _r2.json().get('value', [])
                                        if _me:
                                            _lines.append('Outlook takvimi:')
                                            for _e in _me:
                                                _t = _e.get('subject','Basliksiz')
                                                _s = _e.get('start',{}).get('dateTime','')
                                                try:
                                                    _edt = _dt.fromisoformat(_s)
                                                    _s = _edt.strftime('%d %B %Y %H:%M')
                                                except: pass
                                                _lines.append(f'- {_s} : {_t}')
                                    except Exception as _me2:
                                        _lines.append(f'Outlook takvim hatasi: {_me2}')
                            cal_response = chr(10).join(_lines) if _lines else 'Takvimde yaklasan etkinlik yok.'
                        else:
                            cal_response = 'Takvim bagli degil. Ayarlardan Google veya Microsoft takviminizi baglayin.'
                    else:
                        cal_response = assistant.process(text)
                    _history.save_message(session_id, "assistant", cal_response, user_id)
                    await websocket.send_text(json.dumps({"type": "response", "text": cal_response}))
                    continue
                # DB geçmişini LLM'e ilet + resolved text kullan
                db_history = [{"role": m["role"], "content": m["content"]} for m in session_history[-8:]]
                # Kimlik sorularini direkt SOHBET olarak isle, web aramasi yapma
                _kimlik_sorulari = ["sen kimsin", "kim yaratti", "amacin ne", "ne yapabilirsin", "nasil calisiyorsun", "kim gelistirdi", "jarvis kimdir", "sen neydin", "seni yaratan"]
                from core.router import normalize as _norm
                _rt_norm = _norm(resolved_text.lower())
                if any(k in _rt_norm for k in _kimlik_sorulari):
                    result = {"kategori": "SOHBET", "yanit": None, "not_icerik": None, "hatirlatma_zamani": None, "medya_sorgu": None, "rezervasyon_detay": None}
                else:
                    result = assistant.llm.process(resolved_text, db_history, mode=chat_mode)
                category = result.get("kategori", "SOHBET")
                text_norm = normalize(text)
                bilgi = ["nedir","kimdir","nasil","anlat","kim","neden","hava","haber","sicaklik","acikla","dusun","fikir","ne dusunuyorsun","ile ilgili","hakkinda","ne biliyorsun","yorumun","degerlendirme","onerir","tavsiye"]
                use_stream = category in ["WEB_ARAMA","SOHBET"] or any(k in text_norm for k in bilgi)
                if use_stream:
                    if any(k in text_norm for k in ["hava","sicaklik","yagmur"]):
                        raw = assistant.search.weather(text)
                    elif any(k in text_norm for k in ["haber","gundem"]):
                        raw = assistant.search.news(text)
                    elif any(k in text_norm for k in bilgi):
                        raw = assistant.search.search(text)
                    else:
                        raw = ""
                    from datetime import datetime as _dtnow
                    _mode_hint = "Maksimum 3 cumle ile kisa ve oz yanit ver. Madde listesi kullanma." if chat_mode == "hizli" else "Kapsamli, detayli ve analitik yanit ver. Alt basliklar ve ornekler kullan."
                    sistem = f"""Sen Jarvis\'sin, Aktivra tarafindan gelistirilmis Turkce konusan zeki ve sicak bir yapay zeka asistanisin.
KIMLIGIN: Adin Jarvis. Seni Aktivra gelistirdi. Kendini "Ben Jarvis, Aktivra'nin yapay zeka asistaniyim." diye tanit. Sicak ve samimi konusursun. Web arama sonuclarinda video linkleri veya YouTube onerileri VERME, sadece bilgi ver.
MOD: {_mode_hint}
TURKCE KURALI: KESINLIKLE sadece Turkce yaz. Asla Cince, Japonca veya baska dil karakteri kullanma.
Markdown kullan: basliklar icin ##, kalin icin **bold**, listeler icin -.
Bugun: {_dtnow.now().strftime('%Y-%m-%d %H:%M')}"""
                    # Context history formatla
                    ctx_msgs = []
                    for m in session_history[-6:]:
                        ctx_msgs.append({"role": m["role"], "content": m["content"]})
                    import re as _re2
                    # Asya dil karakterlerini ve markdown link formatindaki video linklerini temizle
                    raw = _re2.sub(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u3400-\u4dbf]', '', raw)
                    raw = _re2.sub(r'\[.*?\]\(https?://.*?\)', '', raw)  # markdown linkleri kaldir
                    raw = _re2.sub(r'https?://\S+', '', raw)  # diger linkleri kaldir
                    if raw and len(raw) > 20:
                        prompt = f"Soru: {resolved_text}\nArama sonucu (sadece Turkce kullan): {raw[:500]}\nYALNIZCA TURKCE cevapla. Asla Cince veya yabanci karakter yazma."
                    else:
                        prompt = f"Soru: {resolved_text}\nYALNIZCA TURKCE olarak cevapla."
                    full_text = ""
                    # full_text temizleyici fonksiyon
                    def _clean_tr(t):
                        import re as _rec
                        t = _rec.sub(r'[一-鿿぀-ゟ゠-ヿ가-힯㐀-䶿＀-￯]', '', t)
                        t = _rec.sub(r'https?://\S+', '', t)
                        t = _rec.sub(r'\[.*?\]\(.*?\)', '', t)
                        # Çince cümle kalıntılarını temizle (noktalama + boşluk)
                        t = _rec.sub(r'[。，、；：？！""''【】《》（）]+', ' ', t)
                        t = _rec.sub(r'\s{3,}', ' ', t)
                        return t.strip()
                    await websocket.send_text(json.dumps({"type": "stream_start"}))
                    async with httpx.AsyncClient(timeout=60) as client:
                        async with client.stream("POST", "http://172.17.0.1:11434/api/chat", json={
                            "model": config.llm_model,
                            "messages": [
                                {"role": "system", "content": sistem},
                                *ctx_msgs[:-1],  # önceki geçmiş (son user hariç)
                                {"role": "user", "content": prompt}
                            ],
                            "stream": True,
                        }) as resp:
                            async for line in resp.aiter_lines():
                                if line:
                                    try:
                                        chunk = json.loads(line)
                                        token = chunk.get("message", {}).get("content", "")
                                        if token:
                                            full_text += token
                                            await websocket.send_text(json.dumps({"type": "stream", "text": token}))
                                    except:
                                        pass
                    full_text = _clean_tr(full_text)
                    # Son 150 karakterde soru yoksa konuya gore soru ekle
                    if full_text and full_text.strip() and "?" not in full_text[-150:]:
                        # Konudan anahtar kelime al
                        _konu_kelime = text.strip().split()[0] if text.strip() else "bu konu"
                        # Konuya gore farkli soru sablonlari
                        _soru_sablonlari = [
                            f"\n\nPeki {_konu_kelime} ile ilgili kişisel deneyiminiz var mı?",
                            f"\n\nBu konuda daha ayrıntılı bir şey sormak ister misiniz?",
                            f"\n\nSizin bu konudaki görüşünüz nedir?",
                        ]
                        import hashlib as _hlib
                        _idx = int(_hlib.md5(full_text[-30:].encode("utf-8", errors="ignore")).hexdigest()[:4], 16) % len(_soru_sablonlari)
                        _ek_soru = _soru_sablonlari[_idx]
                        full_text = full_text + _ek_soru
                        # Soruyu stream token olarak gonder ki frontend gorsun
                        await websocket.send_text(json.dumps({"type": "stream", "text": _ek_soru}))
                    await websocket.send_text(json.dumps({"type": "stream_end", "text": full_text}))
                    assistant.update_history(text, full_text)
                    _history.save_message(session_id, "assistant", full_text, user_id)
                    # İlk mesajsa başlık üret
                    if is_first_msg and full_text:
                        import asyncio
                        asyncio.create_task(generate_session_title(session_id, text, full_text))
                    # İlk mesajsa başlık üret
                    if is_first_msg and full_text:
                        import asyncio
                        asyncio.create_task(generate_session_title(session_id, text, full_text))
                else:
                    response = assistant.process(text)
                    assistant.update_history(text, response)
                    # SOHBET modunda da soru ekle
                    if response and "?" not in response[-150:]:
                        _konu = text.strip().split()[0] if text.strip() else "bu konu"
                        _ekler = [
                            f"\n\nPeki {_konu} ile ilgili kişisel deneyiminiz var mı?",
                            f"\n\nBu konuda daha fazla bilgi ister misiniz?",
                            f"\n\nSizin bu konudaki görüşünüz nedir?",
                        ]
                        import hashlib as _h2
                        _i2 = int(_h2.md5(response[-20:].encode()).hexdigest()[:4], 16) % len(_ekler)
                        response += _ekler[_i2]
                    await websocket.send_text(json.dumps({"type": "response", "text": response}))
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "response", "text": str(e)}))
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "text": str(e)}))
        except:
            pass

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        from faster_whisper import WhisperModel
        if not hasattr(app.state, "whisper"):
            app.state.whisper = WhisperModel("small", device="cpu", compute_type="int8")
        data = await audio.read()
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        segments, _ = app.state.whisper.transcribe(tmp_path, language="tr")
        text = " ".join([s.text for s in segments]).strip()
        os.unlink(tmp_path)
        return {"text": text, "status": "ok"}
    except Exception as e:
        return {"text": "", "error": str(e), "status": "error"}

import base64
from services.tts_elevenlabs import ElevenLabsTTS, CHARACTERS

_tts_client = None

def get_tts():
    global _tts_client
    if _tts_client is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if api_key:
            _tts_client = ElevenLabsTTS(api_key)
    return _tts_client

@app.get("/tts/characters")
async def get_characters():
    return {"characters": CHARACTERS}

@app.post("/tts/synthesize")
async def synthesize_speech(request: dict):
    text = request.get("text", "")
    character = request.get("character", "jarvis")
    if not text:
        return {"error": "text required"}
    tts = get_tts()
    if not tts:
        return {"error": "TTS not configured"}
    try:
        audio = tts.synthesize(text, character)
        if audio:
            return {"audio": base64.b64encode(audio).decode(), "format": "mp3"}
        return {"error": "synthesis failed"}
    except Exception as e:
        return {"error": str(e)}

# Calendar endpoints
from services.calendar_service import CalendarService
_calendar = CalendarService()

@app.get("/calendar/auth/google")
async def google_auth():
    try:
        from google_auth_oauthlib.flow import Flow
        import json
        flow = Flow.from_client_secrets_file(
            '/app/data/google_credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        return {"auth_url": auth_url, "status": "ok"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/calendar/auth/google/token")
async def google_token(request: dict):
    try:
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        import os
        flow = Flow.from_client_secrets_file(
            '/app/data/google_credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        flow.fetch_token(code=request.get('code'))
        creds = flow.credentials
        os.makedirs('/app/data', exist_ok=True)
        with open('/app/data/google_token.json', 'w') as f:
            f.write(creds.to_json())
        _calendar.google_service = build('calendar', 'v3', credentials=creds)
        _calendar.provider = 'google'
        return {"status": "ok", "message": "Google Calendar baglandi!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/calendar/events")
async def get_events(days: int = 7):
    try:
        events = _calendar.get_events(days)
        formatted = _calendar.format_events(events)
        return {"events": events, "formatted": formatted, "count": len(events)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/calendar/add")
async def add_event(request: dict):
    try:
        from datetime import datetime
        title = request.get('title', '')
        start_str = request.get('start', '')
        description = request.get('description', '')
        start = datetime.fromisoformat(start_str)
        success = _calendar.add_google_event(title, start, description=description)
        return {"status": "ok" if success else "error"}
    except Exception as e:
        return {"error": str(e)}

# Calendar endpoints
from services.calendar_service import CalendarService
_calendar = CalendarService()

_pkce_verifier = None

@app.get("/calendar/auth/google")
async def google_auth():
    global _pkce_verifier
    try:
        import json, base64, hashlib, secrets
        from urllib.parse import urlencode
        with open('/app/data/google_credentials.json') as f:
            client_config = json.load(f)
        client_id = client_config['installed']['client_id']
        
        # PKCE code verifier ve challenge olustur
        _pkce_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(_pkce_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        # Verifier'i dosyaya kaydet
        with open('/app/data/pkce_verifier.txt', 'w') as vf:
            vf.write(_pkce_verifier)
        
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'scope': 'https://www.googleapis.com/auth/calendar',
            'access_type': 'offline',
            'prompt': 'consent',
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
        }
        auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
        return {"auth_url": auth_url, "status": "ok"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/calendar/auth/google/token")
async def google_token(request: dict):
    try:
        import json, requests as req, os
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        with open('/app/data/google_credentials.json') as f:
            client_config = json.load(f)['installed']

        # Verifier'i dosyadan oku
        verifier = None
        try:
            with open('/app/data/pkce_verifier.txt', 'r') as vf:
                verifier = vf.read().strip()
        except:
            pass
        token_data_req = {
            'code': request.get('code'),
            'client_id': client_config['client_id'],
            'client_secret': client_config['client_secret'],
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'grant_type': 'authorization_code',
        }
        if verifier:
            token_data_req['code_verifier'] = verifier
        token_res = req.post('https://oauth2.googleapis.com/token', data=token_data_req)
        token_data = token_res.json()
        if 'error' in token_data:
            return {"error": token_data['error_description']}

        os.makedirs('/app/data', exist_ok=True)
        with open('/app/data/google_token.json', 'w') as f:
            json.dump(token_data, f)

        creds = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_config['client_id'],
            client_secret=client_config['client_secret'],
        )
        _calendar.google_service = build('calendar', 'v3', credentials=creds)
        _calendar.provider = 'google'
        return {"status": "ok", "message": "Google Calendar baglandi!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/calendar/events")
async def get_events(days: int = 7):
    try:
        events = _calendar.get_events(days)
        formatted = _calendar.format_events(events)
        return {"events": events, "formatted": formatted, "count": len(events)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/calendar/add")
async def add_event(request: dict):
    try:
        from datetime import datetime
        title = request.get('title', '')
        start_str = request.get('start', '')
        description = request.get('description', '')
        start = datetime.fromisoformat(start_str)
        success = _calendar.add_google_event(title, start, description=description)
        return {"status": "ok" if success else "error"}
    except Exception as e:
        return {"error": str(e)}

import msal

OUTLOOK_CLIENT_ID = "9b1ecc4d-c0cc-4123-8ec1-522c8f278ecf"
OUTLOOK_TENANT_ID = "46642cdf-f4a1-45ee-bd35-1defe8fd90a0"
OUTLOOK_CLIENT_SECRET = "***REMOVED***"
OUTLOOK_SCOPES = ["Calendars.ReadWrite", "User.Read"]
_outlook_token = None
_outlook_flow = None

@app.get("/calendar/auth/outlook")
async def outlook_auth():
    global _outlook_flow
    try:
        app_msal = msal.PublicClientApplication(
            OUTLOOK_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/common"
        )
        _outlook_flow = app_msal.initiate_device_flow(scopes=OUTLOOK_SCOPES)
        return {
            "status": "ok",
            "message": _outlook_flow.get("message", ""),
            "user_code": _outlook_flow.get("user_code", ""),
            "verification_url": _outlook_flow.get("verification_uri", "https://microsoft.com/devicelogin")
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/calendar/auth/outlook/token")
async def outlook_token():
    global _outlook_flow, _outlook_token
    try:
        app_msal = msal.PublicClientApplication(
            OUTLOOK_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/common"
        )
        result = app_msal.acquire_token_by_device_flow(_outlook_flow)
        if "access_token" in result:
            _outlook_token = result["access_token"]
            import json, os
            os.makedirs("/app/data", exist_ok=True)
            with open("/app/data/outlook_token.json", "w") as f:
                json.dump(result, f)
            return {"status": "ok", "message": "Outlook Calendar baglandi!"}
        return {"error": result.get("error_description", "Token alinamadi")}
    except Exception as e:
        return {"error": str(e)}

@app.get("/calendar/events/outlook")
async def get_outlook_events(days: int = 7):
    global _outlook_token
    try:
        import requests as req, json
        from datetime import datetime, timedelta
        if not _outlook_token:
            if os.path.exists("/app/data/outlook_token.json"):
                with open("/app/data/outlook_token.json") as f:
                    data = json.load(f)
                _outlook_token = data.get("access_token")
        if not _outlook_token:
            return {"error": "Outlook bagli degil"}
        headers = {"Authorization": f"Bearer {_outlook_token}"}
        now = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
        url = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={now}&endDateTime={end}&$top=20&$orderby=start/dateTime"
        res = req.get(url, headers=headers)
        events = res.json().get("value", [])
        if not events:
            return {"formatted": "Outlook takviminde yaklasan etkinlik yok.", "events": []}
        lines = ["Outlook takvimi:"]
        for e in events:
            title = e.get("subject", "Basliksiz")
            start = e.get("start", {}).get("dateTime", "")
            try:
                dt = datetime.fromisoformat(start)
                start = dt.strftime("%d %B %Y %H:%M")
            except Exception:
                pass
            lines.append("- " + start + " : " + title)
        return {"formatted": chr(10).join(lines), "events": events}
    except Exception as e:
        return {"error": str(e)}

# Sohbet gecmisi endpoints
from services.history_service import HistoryService
_history = HistoryService()

@app.get("/history/sessions")
async def get_sessions(user_id: int = None):
    return {"sessions": _history.get_all_sessions(user_id)}

@app.get("/history/session/{session_id}")
async def get_session(session_id: str):
    return {"messages": _history.get_session(session_id)}

@app.delete("/history/session/{session_id}")
async def delete_session(session_id: str):
    success = _history.delete_session(session_id)
    return {"status": "ok" if success else "error"}

@app.get("/history/search")
async def search_history(q: str):
    return {"results": _history.search_history(q)}

from services.auth_service import AuthService
_auth = AuthService()

@app.post("/auth/register")
async def register(request: dict):
    email = request.get("email", "")
    isim = request.get("isim", "")
    password = request.get("password", "")
    if not email or not password:
        return {"error": "Email ve sifre zorunlu"}
    return _auth.register(email, isim, password)

@app.post("/auth/verify-email")
async def verify_email(request: dict):
    token = request.get("token", "")
    if not token:
        return {"error": "Token zorunlu"}
    return _auth.verify_email(token)
@app.post("/auth/resend-verification")
async def resend_verification(request: dict):
    email = request.get("email", "")
    if not email:
        return {"error": "Email zorunlu"}
    return _auth.resend_verification(email)
@app.get("/auth/verify-email")
async def verify_email_get(token: str):
    result = _auth.verify_email(token)
    if "error" in result:
        return RedirectResponse(url="https://aktivra.com/verify-error")
    return RedirectResponse(url="https://aktivra.com/verify-success")
@app.post("/auth/login")
async def login(request: dict):
    email = request.get("email", "")
    password = request.get("password", "")
    return _auth.login(email, password)

@app.post("/auth/change-password")
async def change_password(request: dict):
    token = request.get("token", "")
    current_password = request.get("current_password", "")
    new_password = request.get("new_password", "")
    if not token or not new_password:
        return {"error": "Token ve yeni sifre zorunlu"}
    if len(new_password) < 6:
        return {"error": "Sifre en az 6 karakter olmali"}
    user = _auth.verify_token(token)
    if "error" in user:
        return {"error": "Gecersiz token"}
    from database.db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    row = db.execute(text("SELECT email, isim FROM kullanicilar WHERE id = :id"), {"id": user["user_id"]}).fetchone()
    if not row:
        db.close()
        return {"error": "Kullanici bulunamadi"}
    email, isim = row
    db.close()
    result = _auth.request_password_change(email, isim, user["user_id"], new_password)
    return result

@app.get("/auth/confirm-password-change")
async def confirm_password_change(token: str):
    result = _auth.confirm_password_change(token)
    if result.get("success"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="https://aktivra.com/?pw_changed=1")
    return RedirectResponse(url="https://aktivra.com/?pw_error=1")
@app.post("/auth/logout")
async def logout(request: dict):
    token = request.get("token", "")
    _auth.logout(token)
    return {"status": "ok"}

@app.get("/auth/me")
async def get_me(token: str):
    return _auth.verify_token(token)

import asyncio

async def refresh_outlook_token():
    while True:
        try:
            import requests, json, os
            token_path = '/app/data/outlook_token.json'
            if os.path.exists(token_path):
                with open(token_path) as f:
                    data = json.load(f)
                rt = data.get('refresh_token', '')
                if rt:
                    res = requests.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data={
                        'client_id': '9b1ecc4d-c0cc-4123-8ec1-522c8f278ecf',
                        'refresh_token': rt,
                        'grant_type': 'refresh_token',
                        'scope': 'Calendars.ReadWrite User.Read offline_access',
                    })
                    result = res.json()
                    if 'access_token' in result:
                        with open(token_path, 'w') as f:
                            json.dump(result, f)
                        print('Outlook token otomatik yenilendi!')
        except Exception as e:
            print(f'Token refresh hatasi: {e}')
        await asyncio.sleep(3300)  # Her 55 dakikada bir

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(refresh_outlook_token())

ADMIN_TOKEN = "***REMOVED***"

def verify_admin(token: str):
    return token == ADMIN_TOKEN

@app.get("/admin/stats")
async def admin_stats(token: str):
    if not verify_admin(token):
        return {"error": "Yetkisiz"}
    try:
        from database.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        users = db.execute(text("SELECT COUNT(*) FROM kullanicilar")).fetchone()[0]
        sessions = db.execute(text("SELECT COUNT(DISTINCT session_id) FROM sohbet_gecmisi")).fetchone()[0]
        messages = db.execute(text("SELECT COUNT(*) FROM sohbet_gecmisi")).fetchone()[0]
        notes = db.execute(text("SELECT COUNT(*) FROM notlar")).fetchone()[0]
        recent_users = db.execute(text(
            "SELECT id, isim, email, created_at, last_login FROM kullanicilar ORDER BY created_at DESC LIMIT 20"
        )).fetchall()
        recent_sessions = db.execute(text(
            "SELECT sg.session_id, MIN(sg.created_at) as started, COUNT(*) as msg_count, COALESCE(st.title, LEFT((SELECT content FROM sohbet_gecmisi s2 WHERE s2.session_id = sg.session_id AND s2.role = 'user' ORDER BY s2.created_at ASC LIMIT 1), 60)) as preview FROM sohbet_gecmisi sg LEFT JOIN session_titles st ON sg.session_id = st.session_id GROUP BY sg.session_id, st.title ORDER BY started DESC LIMIT 20"
        )).fetchall()
        db.close()
        return {
            "stats": {"users": users, "sessions": sessions, "messages": messages, "notes": notes},
            "users": [{"id": r[0], "isim": r[1], "email": r[2], "created_at": str(r[3]), "last_login": str(r[4])} for r in recent_users],
            "sessions": [{"session_id": r[0], "started": str(r[1]), "msg_count": r[2], "preview": r[3]} for r in recent_sessions],
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin/system")
async def admin_system(token: str):
    if not verify_admin(token):
        return {"error": "Yetkisiz"}
    try:
        import psutil, subprocess
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        ollama_ok = False
        try:
            import requests as req
            r = req.get('http://172.17.0.1:11434/api/tags', timeout=2)
            ollama_ok = r.status_code == 200
        except: pass
        return {
            "cpu": cpu,
            "memory": {"total": mem.total, "used": mem.used, "percent": mem.percent},
            "disk": {"total": disk.total, "used": disk.used, "percent": disk.percent},
            "services": {
                "api": True,
                "ollama": ollama_ok,
                "postgres": True,
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.delete("/admin/user/{user_id}")
async def admin_delete_user(user_id: int, token: str):
    if not verify_admin(token):
        return {"error": "Yetkisiz"}
    try:
        from database.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("DELETE FROM kullanicilar WHERE id = :id"), {"id": user_id})
        db.commit()
        db.close()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}

import json as _json

GOOGLE_WEB_CREDS = '/app/data/google_web_credentials.json'
MICROSOFT_CLIENT_ID = '9b1ecc4d-c0cc-4123-8ec1-522c8f278ecf'
MICROSOFT_CLIENT_SECRET = '***REMOVED***'
REDIRECT_BASE = 'https://aktivra.com/api'

@app.get("/auth/google/url")
async def google_auth_url(user_id: int):
    try:
        import base64, hashlib, secrets
        from urllib.parse import urlencode
        with open(GOOGLE_WEB_CREDS) as f:
            cfg = _json.load(f)['web']
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        from database.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("INSERT INTO kullanici_takvim_tokenlar (kullanici_id, provider, access_token, refresh_token) VALUES (:u, :p, :a, :r) ON CONFLICT (kullanici_id, provider) DO UPDATE SET refresh_token = :r"), {"u": user_id, "p": "google_verifier", "a": "", "r": verifier})
        db.commit()
        db.close()
        params = {
            'response_type': 'code',
            'client_id': cfg['client_id'],
            'redirect_uri': REDIRECT_BASE + '/auth/google/callback',
            'scope': 'https://www.googleapis.com/auth/calendar',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': str(user_id),
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
        }
        url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
        return {"url": url}
    except Exception as e:
        return {"error": str(e)}

@app.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    try:
        import requests as _req
        from database.db import SessionLocal
        from sqlalchemy import text
        from datetime import datetime, timedelta
        user_id = int(state)
        with open(GOOGLE_WEB_CREDS) as f:
            cfg = _json.load(f)['web']
        db = SessionLocal()
        row = db.execute(text("SELECT refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider = 'google_verifier'"), {"u": user_id}).fetchone()
        verifier = row[0] if row else None
        token_data = {
            'code': code,
            'client_id': cfg['client_id'],
            'client_secret': cfg['client_secret'],
            'redirect_uri': REDIRECT_BASE + '/auth/google/callback',
            'grant_type': 'authorization_code',
        }
        if verifier:
            token_data['code_verifier'] = verifier
        res = _req.post('https://oauth2.googleapis.com/token', data=token_data)
        tokens = res.json()
        print(f"Google tokens keys: {list(tokens.keys())}")
        if 'access_token' not in tokens:
            return {"error": tokens.get('error_description', 'Token alinamadi')}
        expires_at = datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))
        try:
            db.execute(text("INSERT INTO kullanici_takvim_tokenlar (kullanici_id, provider, access_token, refresh_token, expires_at) VALUES (:u, :p, :a, :r, :e) ON CONFLICT (kullanici_id, provider) DO UPDATE SET access_token = :a, refresh_token = :r, expires_at = :e"), {"u": user_id, "p": "google", "a": tokens['access_token'], "r": tokens.get('refresh_token', ''), "e": expires_at})
            db.commit()
            print(f"Google token DB kayit OK! user_id={user_id}")
        except Exception as db_err:
            print(f"Google token DB HATA: {db_err}")
        finally:
            db.close()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="https://aktivra.com/?calendar=connected", status_code=302)
    except Exception as e:
        return {"error": str(e)}

@app.get("/auth/microsoft/url")
async def microsoft_auth_url(user_id: int):
    try:
        from urllib.parse import urlencode
        params = {
            'client_id': MICROSOFT_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_BASE + '/auth/microsoft/callback',
            'scope': 'Calendars.ReadWrite User.Read offline_access',
            'state': str(user_id),
            'response_mode': 'query',
        }
        url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?' + urlencode(params)
        return {"url": url}
    except Exception as e:
        return {"error": str(e)}

@app.get("/auth/microsoft/callback")
async def microsoft_callback(code: str, state: str):
    try:
        import requests as _req
        from database.db import SessionLocal
        from sqlalchemy import text
        from datetime import datetime, timedelta
        user_id = int(state)
        res = _req.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data={
            'client_id': MICROSOFT_CLIENT_ID,
            'client_secret': MICROSOFT_CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_BASE + '/auth/microsoft/callback',
            'grant_type': 'authorization_code',
        })
        tokens = res.json()
        if 'access_token' not in tokens:
            return {"error": tokens.get('error_description', 'Token alinamadi')}
        expires_at = datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))
        db = SessionLocal()
        db.execute(text("INSERT INTO kullanici_takvim_tokenlar (kullanici_id, provider, access_token, refresh_token, expires_at) VALUES (:u, :p, :a, :r, :e) ON CONFLICT (kullanici_id, provider) DO UPDATE SET access_token = :a, refresh_token = :r, expires_at = :e"), {"u": user_id, "p": "microsoft", "a": tokens['access_token'], "r": tokens.get('refresh_token', ''), "e": expires_at})
        db.commit()
        db.close()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="https://aktivra.com/?calendar=connected")
    except Exception as e:
        return {"error": str(e)}

@app.get("/calendar/user/{user_id}/events")
async def get_user_calendar_events(user_id: int, token: str, days: int = 7):
    try:
        user = _auth.verify_token(token)
        if "error" in user or user["user_id"] != user_id:
            return {"error": "Yetkisiz"}
        import requests as _req
        from database.db import SessionLocal
        from sqlalchemy import text
        from datetime import datetime, timedelta
        db = SessionLocal()
        rows = db.execute(text("SELECT provider, access_token, refresh_token, expires_at FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google', 'microsoft')"), {"u": user_id}).fetchall()
        db.close()
        events = []
        for row in rows:
            provider, access_token, refresh_token, expires_at = row
            if provider == 'google':
                from googleapiclient.discovery import build
                from google.oauth2.credentials import Credentials
                with open(GOOGLE_WEB_CREDS) as f:
                    cfg = _json.load(f)['web']
                creds = Credentials(token=access_token, refresh_token=refresh_token, token_uri='https://oauth2.googleapis.com/token', client_id=cfg['client_id'], client_secret=cfg['client_secret'])
                service = build('calendar', 'v3', credentials=creds)
                now = datetime.utcnow().isoformat() + 'Z'
                end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
                result = service.events().list(calendarId='primary', timeMin=now, timeMax=end, maxResults=10, singleEvents=True, orderBy='startTime').execute()
                for e in result.get('items', []):
                    events.append({"provider": "Google", "title": e.get('summary', 'Basliksiz'), "start": e.get('start', {}).get('dateTime', e.get('start', {}).get('date', ''))})
            elif provider == 'microsoft':
                headers = {'Authorization': 'Bearer ' + access_token}
                now = datetime.utcnow().isoformat() + 'Z'
                end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
                res = _req.get(f'https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={now}&endDateTime={end}&$top=10&$orderby=start/dateTime', headers=headers)
                for e in res.json().get('value', []):
                    events.append({"provider": "Microsoft", "title": e.get('subject', 'Basliksiz'), "start": e.get('start', {}).get('dateTime', '')})
        return {"events": events, "count": len(events)}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/calendar/disconnect/{provider}")
async def disconnect_calendar(provider: str, user_id: int, token: str):
    try:
        user = _auth.verify_token(token)
        if "error" in user or user["user_id"] != user_id:
            return {"error": "Yetkisiz"}
        from database.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("DELETE FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider = :p"), {"u": user_id, "p": provider})
        db.commit()
        db.close()
        return {"status": "ok", "message": provider + " takvim baglantisi kesildi!"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/calendar/status/{user_id}")
async def calendar_status(user_id: int, token: str):
    try:
        user = _auth.verify_token(token)
        if "error" in user or user["user_id"] != user_id:
            return {"error": "Yetkisiz"}
        from database.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        rows = db.execute(text("SELECT provider FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google', 'microsoft')"), {"u": user_id}).fetchall()
        db.close()
        providers = [r[0] for r in rows]
        return {"google": "google" in providers, "microsoft": "microsoft" in providers}
    except Exception as e:
        return {"error": str(e)}


@app.get("/calendar/events/today")
async def calendar_events_today(user_id: int, token: str = ""):
    try:
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _text
        from datetime import datetime as _dt, timedelta as _td
        import requests as _req
        _db = _SL()
        _rows = _db.execute(_text("SELECT provider, access_token, refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google','microsoft')"), {"u": user_id}).fetchall()
        _db.close()
        events = []
        now = _dt.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0)
        end_of_day   = now.replace(hour=23, minute=59, second=59)
        for row in _rows:
            prov, at, rt = row
            if prov == 'google':
                try:
                    from google.oauth2.credentials import Credentials
                    from googleapiclient.discovery import build
                    import json as _js
                    with open(GOOGLE_WEB_CREDS) as f:
                        cfg = _js.load(f)['web']
                    creds = Credentials(token=at, refresh_token=rt, token_uri='https://oauth2.googleapis.com/token', client_id=cfg['client_id'], client_secret=cfg['client_secret'])
                    svc = build('calendar', 'v3', credentials=creds)
                    evts = svc.events().list(calendarId='primary', timeMin=start_of_day.isoformat()+'Z', timeMax=end_of_day.isoformat()+'Z', maxResults=20, singleEvents=True, orderBy='startTime').execute().get('items', [])
                    for e in evts:
                        events.append({"id": e.get('id'), "title": e.get('summary', 'Başlıksız'), "start": e.get('start',{}).get('dateTime', e.get('start',{}).get('date')), "end": e.get('end',{}).get('dateTime', e.get('end',{}).get('date')), "provider": "Google"})
                except Exception as ge:
                    print(f"Google events error: {ge}")
            elif prov == 'microsoft':
                try:
                    hdrs = {'Authorization': 'Bearer ' + at}
                    r = _req.get(f'https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_of_day.isoformat()}Z&endDateTime={end_of_day.isoformat()}Z&$top=20&$orderby=start/dateTime', headers=hdrs)
                    for e in r.json().get('value', []):
                        events.append({"id": e.get('id'), "title": e.get('subject', 'Başlıksız'), "start": e.get('start',{}).get('dateTime'), "end": e.get('end',{}).get('dateTime'), "provider": "Outlook"})
                except Exception as me:
                    print(f"MS events error: {me}")
        events.sort(key=lambda x: x.get('start') or '')
        return {"events": events}
    except Exception as e:
        return {"events": [], "error": str(e)}

@app.get("/calendar/events/today")
async def calendar_events_today(user_id: int, token: str = ""):
    try:
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _text
        from datetime import datetime as _dt, timedelta as _td
        import requests as _req
        _db = _SL()
        _rows = _db.execute(_text("SELECT provider, access_token, refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google','microsoft')"), {"u": user_id}).fetchall()
        _db.close()
        events = []
        now = _dt.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0)
        end_of_day   = now.replace(hour=23, minute=59, second=59)
        for row in _rows:
            prov, at, rt = row
            if prov == 'google':
                try:
                    from google.oauth2.credentials import Credentials
                    from googleapiclient.discovery import build
                    import json as _js
                    with open(GOOGLE_WEB_CREDS) as f:
                        cfg = _js.load(f)['web']
                    creds = Credentials(token=at, refresh_token=rt, token_uri='https://oauth2.googleapis.com/token', client_id=cfg['client_id'], client_secret=cfg['client_secret'])
                    svc = build('calendar', 'v3', credentials=creds)
                    evts = svc.events().list(calendarId='primary', timeMin=start_of_day.isoformat()+'Z', timeMax=end_of_day.isoformat()+'Z', maxResults=20, singleEvents=True, orderBy='startTime').execute().get('items', [])
                    for e in evts:
                        events.append({"id": e.get('id'), "title": e.get('summary', 'Başlıksız'), "start": e.get('start',{}).get('dateTime', e.get('start',{}).get('date')), "end": e.get('end',{}).get('dateTime', e.get('end',{}).get('date')), "provider": "Google"})
                except Exception as ge:
                    print(f"Google events error: {ge}")
            elif prov == 'microsoft':
                try:
                    hdrs = {'Authorization': 'Bearer ' + at}
                    r = _req.get(f'https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_of_day.isoformat()}Z&endDateTime={end_of_day.isoformat()}Z&$top=20&$orderby=start/dateTime', headers=hdrs)
                    for e in r.json().get('value', []):
                        events.append({"id": e.get('id'), "title": e.get('subject', 'Başlıksız'), "start": e.get('start',{}).get('dateTime'), "end": e.get('end',{}).get('dateTime'), "provider": "Outlook"})
                except Exception as me:
                    print(f"MS events error: {me}")
        events.sort(key=lambda x: x.get('start') or '')
        return {"events": events}
    except Exception as e:
        return {"events": [], "error": str(e)}

@app.post("/calendar/add/user")
async def add_event_user(request: dict):
    """Kullanicinin OAuth tokeni ile takvime etkinlik ekler."""
    try:
        from datetime import datetime as _dt2
        user_id    = request.get('user_id')
        title      = request.get('title', 'Etkinlik')
        start_str  = request.get('start', '')
        end_str    = request.get('end', '')
        description= request.get('description', '')
        provider   = request.get('provider', 'google')  # google veya microsoft
        if not user_id or not start_str:
            return {"error": "user_id ve start zorunlu"}
        from database.db import SessionLocal as _SL4
        from sqlalchemy import text as _t4
        _db4 = _SL4()
        row = _db4.execute(_t4("SELECT access_token, refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider = :p"), {"u": user_id, "p": provider}).fetchone()
        _db4.close()
        if not row:
            return {"error": f"{provider} takvimi bagli degil"}
        at, rt = row
        start_dt = _dt2.fromisoformat(start_str)
        end_dt   = _dt2.fromisoformat(end_str) if end_str else _dt2.fromisoformat(start_str.replace(start_str[11:16], f"{int(start_str[11:13])+1:02d}{start_str[13:16]}"))
        if provider == 'google':
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            import json as _js5
            with open(GOOGLE_WEB_CREDS) as f:
                cfg = _js5.load(f)['web']
            creds = Credentials(token=at, refresh_token=rt, token_uri='https://oauth2.googleapis.com/token', client_id=cfg['client_id'], client_secret=cfg['client_secret'])
            svc = build('calendar', 'v3', credentials=creds)
            event = {'summary': title, 'description': description, 'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Istanbul'}, 'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Istanbul'}}
            created = svc.events().insert(calendarId='primary', body=event).execute()
            return {"status": "ok", "event_id": created.get('id'), "title": title, "start": start_str}
        elif provider == 'microsoft':
            import requests as _req5
            hdrs = {'Authorization': 'Bearer ' + at, 'Content-Type': 'application/json'}
            body = {"subject": title, "body": {"contentType": "HTML", "content": description}, "start": {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Istanbul"}, "end": {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Istanbul"}}
            r = _req5.post('https://graph.microsoft.com/v1.0/me/events', headers=hdrs, json=body)
            if r.status_code in [200, 201]:
                return {"status": "ok", "title": title, "start": start_str}
            return {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


@app.post("/calendar/add/user")
async def add_event_user(request: dict):
    """Kullanicinin OAuth tokeni ile takvime etkinlik ekler."""
    try:
        from datetime import datetime as _dt2
        user_id    = request.get('user_id')
        title      = request.get('title', 'Etkinlik')
        start_str  = request.get('start', '')
        end_str    = request.get('end', '')
        description= request.get('description', '')
        provider   = request.get('provider', 'google')  # google veya microsoft
        if not user_id or not start_str:
            return {"error": "user_id ve start zorunlu"}
        from database.db import SessionLocal as _SL4
        from sqlalchemy import text as _t4
        _db4 = _SL4()
        row = _db4.execute(_t4("SELECT access_token, refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider = :p"), {"u": user_id, "p": provider}).fetchone()
        _db4.close()
        if not row:
            return {"error": f"{provider} takvimi bagli degil"}
        at, rt = row
        start_dt = _dt2.fromisoformat(start_str)
        end_dt   = _dt2.fromisoformat(end_str) if end_str else _dt2.fromisoformat(start_str.replace(start_str[11:16], f"{int(start_str[11:13])+1:02d}{start_str[13:16]}"))
        if provider == 'google':
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            import json as _js5
            with open(GOOGLE_WEB_CREDS) as f:
                cfg = _js5.load(f)['web']
            creds = Credentials(token=at, refresh_token=rt, token_uri='https://oauth2.googleapis.com/token', client_id=cfg['client_id'], client_secret=cfg['client_secret'])
            svc = build('calendar', 'v3', credentials=creds)
            event = {'summary': title, 'description': description, 'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Istanbul'}, 'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Istanbul'}}
            created = svc.events().insert(calendarId='primary', body=event).execute()
            return {"status": "ok", "event_id": created.get('id'), "title": title, "start": start_str}
        elif provider == 'microsoft':
            import requests as _req5
            hdrs = {'Authorization': 'Bearer ' + at, 'Content-Type': 'application/json'}
            body = {"subject": title, "body": {"contentType": "HTML", "content": description}, "start": {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Istanbul"}, "end": {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Istanbul"}}
            r = _req5.post('https://graph.microsoft.com/v1.0/me/events', headers=hdrs, json=body)
            if r.status_code in [200, 201]:
                return {"status": "ok", "title": title, "start": start_str}
            return {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


@app.post("/auth/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), user_id: int = 0, token: str = ""):
    try:
        import os, uuid, base64
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _t
        # Dosyayı base64 olarak DB'ye kaydet
        data = await file.read()
        b64 = base64.b64encode(data).decode()
        mime = file.content_type or "image/jpeg"
        avatar_data = f"data:{mime};base64,{b64}"
        db = _SL()
        db.execute(_t("UPDATE kullanicilar SET avatar_url = :a WHERE id = :u"), {"a": avatar_data, "u": user_id})
        db.commit()
        db.close()
        return {"status": "ok", "avatar_url": avatar_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/notifications/{user_id}")
async def get_notifications(user_id: int, token: str = ""):
    try:
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _t
        db = _SL()
        rows = db.execute(_t(
            "SELECT id, type, title, body, is_read, created_at FROM bildirimler WHERE kullanici_id = :u ORDER BY created_at DESC LIMIT 50"
        ), {"u": user_id}).fetchall()
        db.close()
        return {"notifications": [{"id":r[0],"type":r[1],"title":r[2],"body":r[3],"is_read":r[4],"created_at":str(r[5])} for r in rows]}
    except Exception as e:
        return {"notifications": [], "error": str(e)}

@app.post("/notifications/read/{notif_id}")
async def mark_read(notif_id: int):
    try:
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _t
        db = _SL()
        db.execute(_t("UPDATE bildirimler SET is_read = TRUE WHERE id = :i"), {"i": notif_id})
        db.commit()
        db.close()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/auth/profile")
async def get_profile(token: str):
    try:
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _t
        user = _auth.verify_token(token)
        if "error" in user:
            return {"error": "Gecersiz token"}
        db = _SL()
        row = db.execute(_t("SELECT sifre_hash, google_id, microsoft_id FROM kullanicilar WHERE id = :u"), {"u": user["user_id"]}).fetchone()
        db.close()
        has_password = bool(row and row[0] and len(row[0]) > 10)
        is_oauth = bool(row and (row[1] or row[2]))
        return {**user, "has_password": has_password, "is_oauth": is_oauth}
    except Exception as e:
        return {"error": str(e)}


@app.get("/calendar/events/day")
async def calendar_events_day(user_id: int, date: str = "", token: str = ""):
    """Belirli bir günün etkinliklerini getirir."""
    try:
        from datetime import datetime as _dt2, timedelta as _td2
        import requests as _req
        if date:
            target = _dt2.fromisoformat(date)
        else:
            target = _dt2.utcnow()
        start_of_day = target.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day   = target.replace(hour=23, minute=59, second=59, microsecond=999999)
        from database.db import SessionLocal as _SL
        from sqlalchemy import text as _text
        _db = _SL()
        _rows = _db.execute(_text("SELECT provider, access_token, refresh_token FROM kullanici_takvim_tokenlar WHERE kullanici_id = :u AND provider IN ('google','microsoft')"), {"u": user_id}).fetchall()
        _db.close()
        events = []
        for row in _rows:
            prov, at, rt = row
            if prov == 'google':
                try:
                    from google.oauth2.credentials import Credentials
                    from googleapiclient.discovery import build
                    import json as _js
                    with open(GOOGLE_WEB_CREDS) as f:
                        cfg = _js.load(f)['web']
                    creds = Credentials(token=at, refresh_token=rt, token_uri='https://oauth2.googleapis.com/token', client_id=cfg['client_id'], client_secret=cfg['client_secret'])
                    svc = build('calendar', 'v3', credentials=creds)
                    evts = svc.events().list(calendarId='primary', timeMin=start_of_day.isoformat()+'Z', timeMax=end_of_day.isoformat()+'Z', maxResults=20, singleEvents=True, orderBy='startTime').execute().get('items', [])
                    for e in evts:
                        events.append({"id": e.get('id'), "title": e.get('summary','Başlıksız'), "start": e.get('start',{}).get('dateTime', e.get('start',{}).get('date')), "end": e.get('end',{}).get('dateTime', e.get('end',{}).get('date')), "provider": "Google"})
                except Exception as ge:
                    print(f"Google events error: {ge}")
            elif prov == 'microsoft':
                try:
                    hdrs = {'Authorization': 'Bearer ' + at}
                    r = _req.get(f'https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_of_day.isoformat()}Z&endDateTime={end_of_day.isoformat()}Z&$top=20&$orderby=start/dateTime', headers=hdrs)
                    for e in r.json().get('value', []):
                        events.append({"id": e.get('id'), "title": e.get('subject','Başlıksız'), "start": e.get('start',{}).get('dateTime'), "end": e.get('end',{}).get('dateTime'), "provider": "Outlook"})
                except Exception as me:
                    print(f"MS events error: {me}")
        events.sort(key=lambda x: x.get('start') or '')
        return {"events": events}
    except Exception as e:
        return {"events": [], "error": str(e)}

# ── Login OAuth ──────────────────────────────────────────────────────────────
@app.get("/auth/login/google")
async def login_google():
    try:
        from urllib.parse import urlencode
        with open(GOOGLE_WEB_CREDS) as f:
            cfg = _json.load(f)['web']
        params = {
            'response_type': 'code',
            'client_id': cfg['client_id'],
            'redirect_uri': REDIRECT_BASE + '/auth/login/google/callback',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
        }
        url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url)
    except Exception as e:
        return {"error": str(e)}

@app.get("/auth/login/google/callback")
async def login_google_callback(code: str, state: str = ""):
    try:
        import requests as _req
        with open(GOOGLE_WEB_CREDS) as f:
            cfg = _json.load(f)['web']
        res = _req.post('https://oauth2.googleapis.com/token', data={
            'code': code,
            'client_id': cfg['client_id'],
            'client_secret': cfg['client_secret'],
            'redirect_uri': REDIRECT_BASE + '/auth/login/google/callback',
            'grant_type': 'authorization_code',
        })
        tokens = res.json()
        if 'access_token' not in tokens:
            return RedirectResponse(url='https://aktivra.com/?login_error=google')
        userinfo = _req.get('https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': 'Bearer ' + tokens['access_token']}).json()
        email = userinfo.get('email', '')
        isim  = userinfo.get('name', '')
        sub   = userinfo.get('id', '')
        result = _auth.oauth_login(email, isim, sub, 'google', userinfo.get('picture'))
        if 'error' in result:
            return RedirectResponse(url='https://aktivra.com/?login_error=google')
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"https://aktivra.com/?oauth_token={result['token']}&oauth_user={_json.dumps({'user_id':result['user_id'],'isim':result['isim'],'email':result['email']})}")
    except Exception as e:
        return RedirectResponse(url='https://aktivra.com/?login_error=google')

@app.get("/auth/login/microsoft")
async def login_microsoft():
    try:
        from urllib.parse import urlencode
        params = {
            'client_id': '9b1ecc4d-c0cc-4123-8ec1-522c8f278ecf',
            'response_type': 'code',
            'redirect_uri': REDIRECT_BASE + '/auth/login/microsoft/callback',
            'scope': 'openid email profile User.Read',
            'response_mode': 'query',
        }
        url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?' + urlencode(params)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url)
    except Exception as e:
        return {"error": str(e)}

@app.get("/auth/login/microsoft/callback")
async def login_microsoft_callback(code: str, state: str = ""):
    try:
        import requests as _req
        res = _req.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data={
            'client_id': '9b1ecc4d-c0cc-4123-8ec1-522c8f278ecf',
            'client_secret': '***REMOVED***',
            'code': code,
            'redirect_uri': REDIRECT_BASE + '/auth/login/microsoft/callback',
            'grant_type': 'authorization_code',
        })
        tokens = res.json()
        if 'access_token' not in tokens:
            return RedirectResponse(url='https://aktivra.com/?login_error=microsoft')
        userinfo = _req.get('https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': 'Bearer ' + tokens['access_token']}).json()
        email = userinfo.get('mail') or userinfo.get('userPrincipalName', '')
        isim  = userinfo.get('displayName', '')
        sub   = userinfo.get('id', '')
        result = _auth.oauth_login(email, isim, sub, 'microsoft')
        if 'error' in result:
            return RedirectResponse(url='https://aktivra.com/?login_error=microsoft')
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"https://aktivra.com/?oauth_token={result['token']}&oauth_user={_json.dumps({'user_id':result['user_id'],'isim':result['isim'],'email':result['email']})}")
    except Exception as e:
        return RedirectResponse(url='https://aktivra.com/?login_error=microsoft')
