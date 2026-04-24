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
