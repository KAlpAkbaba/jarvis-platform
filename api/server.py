import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import httpx
import tempfile
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
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
            if not text:
                continue
            try:
                result = assistant.llm.process(text, assistant.context.to_list())
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
                    sistem = "Sen yalnizca TURKCE konusan bir yapay zeka asistansin. KESINLIKLE sadece Turkce kullan."
                    if raw and len(raw) > 20:
                        prompt = f"Soru: {text}\nBilgi: {raw[:600]}\nTURKCE olarak detayli cevapla."
                    else:
                        prompt = f"Soru: {text}\nBu soruyu TURKCE olarak cevapla."
                    full_text = ""
                    await websocket.send_text(json.dumps({"type": "stream_start"}))
                    async with httpx.AsyncClient(timeout=60) as client:
                        async with client.stream("POST", "http://172.17.0.1:11434/api/chat", json={
                            "model": config.llm_model,
                            "messages": [
                                {"role": "system", "content": sistem},
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
