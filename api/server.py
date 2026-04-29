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
                    "UPDATE sohbet_gecmisi SET content = :c WHERE session_id = :s AND id = (SELECT MIN(id) FROM sohbet_gecmisi WHERE session_id = :s AND role = 'user')"
                ), {"c": title, "s": session_id})
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
    """Kısa/belirsiz mesajlara önceki konuyu ekler."""
    words = text.strip().split()
    # 5 kelimeden kısa ve soru işareti içeriyorsa veya
    # "nerede", "ne zaman", "kim", "nasıl", "neden", "ne kadar" ile başlıyorsa
    short_question_starters = ["nerede", "ne zaman", "kim", "nasil", "neden", "ne kadar",
                                "kac", "hangi", "ne ile", "neden", "ne kadar", "kimin",
                                "neye", "neyle", "nereye", "nereden"]
    is_short = len(words) <= 6
    starts_with_question = any(text.lower().startswith(s) for s in short_question_starters)
    has_pronoun = any(w in text.lower() for w in ["bu", "onu", "onun", "bunun", "bunu", "orada", "burasi", "orasi"])

    if (is_short and starts_with_question) or has_pronoun:
        topic = extract_topic(history[:-1] if history else [])  # son user msg hariç
        if topic and topic.lower() not in text.lower():
            # Ana nesneyi bul - son uzun user mesajından ilk birkaç kelime
            topic_words = topic.split()[:4]
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
                    "UPDATE sohbet_gecmisi SET content = :c WHERE session_id = :s AND id = (SELECT MIN(id) FROM sohbet_gecmisi WHERE session_id = :s AND role = 'user')"
                ), {"c": title, "s": session_id})
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
    """Kısa/belirsiz mesajlara önceki konuyu ekler."""
    words = text.strip().split()
    # 5 kelimeden kısa ve soru işareti içeriyorsa veya
    # "nerede", "ne zaman", "kim", "nasıl", "neden", "ne kadar" ile başlıyorsa
    short_question_starters = ["nerede", "ne zaman", "kim", "nasil", "neden", "ne kadar",
                                "kac", "hangi", "ne ile", "neden", "ne kadar", "kimin",
                                "neye", "neyle", "nereye", "nereden"]
    is_short = len(words) <= 6
    starts_with_question = any(text.lower().startswith(s) for s in short_question_starters)
    has_pronoun = any(w in text.lower() for w in ["bu", "onu", "onun", "bunun", "bunu", "orada", "burasi", "orasi"])

    if (is_short and starts_with_question) or has_pronoun:
        topic = extract_topic(history[:-1] if history else [])  # son user msg hariç
        if topic and topic.lower() not in text.lower():
            # Ana nesneyi bul - son uzun user mesajından ilk birkaç kelime
            topic_words = topic.split()[:4]
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
            if not text:
                continue
            # Kullanici mesajini kaydet
            user_id = payload.get("user_id")
            # Session geçmişini yükle
            session_history = load_session_history(session_id)
            # Konu takibi — kısa/belirsiz sorulara önceki konuyu ekle
            resolved_text = resolve_context(text, session_history)
            _history.save_message(session_id, "user", text, user_id)
            # İlk mesaj mı? Başlık üretimi için bayrak
            is_first_msg = len([m for m in session_history if m["role"] == "user"]) == 0
            try:
                # Takvim kontrolu - WebSocket icin
                from core.router import normalize
                text_norm_ws = normalize(text.lower())
                takvim_goster_ws = ["takvim", "etkinlik", "randevu", "ajanda"]
                takvim_ekle_ws = ["takvime ekle", "etkinlik ekle", "randevu ekle"]
                hava_ws = ["hava", "sicaklik", "yagis", "derece"]
                tarih_ws = ["bugun", "saat kac", "tarih", "ayın kaci", "ayin kaci"]
                if any(k in text_norm_ws for k in takvim_ekle_ws) or any(k in text_norm_ws for k in takvim_goster_ws) or any(k in text_norm_ws for k in hava_ws) or any(k in text_norm_ws for k in tarih_ws):
                    if any(k in text_norm_ws for k in takvim_goster_ws) and user_id:
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
                result = assistant.llm.process(resolved_text, db_history)
                category = result.get("kategori", "SOHBET")
                text_norm = normalize(text)
                bilgi = ["nedir","kimdir","nasil","anlat","kim","neden","hava","haber","sicaklik","acikla"]
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
                    sistem = "Sen YALNIZCA TURKCE konusan bir yapay zeka asistansin. Bu cok onemli: ASLA Cince, Japonca, Korece, Ingilizce veya baska dil karakteri yazma. Bir tek Latin alfabesi ve Turkce karakter kullan. Cevap icinde yabanci karakter gorursen o cumleyi sil ve Turkce yaz. Markdown formatini kullan: basliklar icin ##, kalin yazi icin **bold**, listeler icin - kullan."
                    # Context history formatla
                    ctx_msgs = []
                    for m in session_history[-6:]:
                        ctx_msgs.append({"role": m["role"], "content": m["content"]})
                    import re as _re2
                    raw = _re2.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]", "", raw)
                    if raw and len(raw) > 20:
                        prompt = f"Soru: {resolved_text}\nArama sonucu (sadece Turkce kullan): {raw[:500]}\nYALNIZCA TURKCE cevapla. Asla Cince veya yabanci karakter yazma."
                    else:
                        prompt = f"Soru: {resolved_text}\nYALNIZCA TURKCE olarak cevapla."
                    full_text = ""
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
    if not token or not current_password or not new_password:
        return {"error": "Tum alanlar zorunlu"}
    if len(new_password) < 6:
        return {"error": "Sifre en az 6 karakter olmali"}
    user = _auth.verify_token(token)
    if "error" in user:
        return {"error": "Gecersiz token"}
    from database.db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    row = db.execute(text("SELECT sifre_hash FROM kullanicilar WHERE id = :id"), {"id": user["user_id"]}).fetchone()
    if not row or not _auth.verify_password(current_password, row[0] or ""):
        db.close()
        return {"error": "Mevcut sifre yanlis"}
    new_hash = _auth.hash_password(new_password)
    db.execute(text("UPDATE kullanicilar SET sifre_hash = :h WHERE id = :id"), {"h": new_hash, "id": user["user_id"]})
    db.commit()
    db.close()
    return {"success": True}
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
            "SELECT session_id, MIN(created_at) as started, COUNT(*) as msg_count, LEFT(MAX(CASE WHEN role='user' THEN content END), 60) as preview FROM sohbet_gecmisi GROUP BY session_id ORDER BY started DESC LIMIT 20"
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
