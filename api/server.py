import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from core.config import config

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Jarvis Platform", version="1.0.0")

try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except:
    pass

active_connections = []


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        assistant = Assistant()
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            text = payload.get("text", "")
            if not text:
                continue
            response = assistant.process(text)
            assistant.update_history(text, response)
            await websocket.send_text(json.dumps({
                "type": "response",
                "text": response
            }))
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "text": str(e)}))
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)


