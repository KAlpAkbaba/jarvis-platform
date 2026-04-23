![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

# Jarvis Platform

A modular Turkish AI assistant platform supporting voice, text, and API-based interaction.

This project combines speech recognition, local LLM-based intent classification, multi-skill routing, and text-to-speech synthesis into a single extensible system.

---

## 🎯 Vision

Jarvis Platform aims to become a fully local, privacy-first AI assistant
capable of replacing cloud-based assistants by running entirely on user-owned infrastructure.

---

## 🚀 Features

- 🎤 Real-time Speech-to-Text (Whisper Large v3, GPU-accelerated)
- 🧠 Offline-first LLM intent classification (Ollama, privacy-friendly)
- 🔊 Text-to-Speech (Piper / XTTS)
- 🧩 Modular skill system:
  - Notes & reminders
  - Media control (YouTube, etc.)
  - Web search (SearXNG / fallback)
  - Weather information
  - Reservation workflows
- 🌐 WebSocket & API support
- 🖥️ CLI-based assistant interface
- 🗄️ PostgreSQL-backed persistence
- 🔁 Context-aware conversation flow

---

## 🧠 Architecture

![Architecture](docs/jarvis_platform_v3.svg)

This diagram represents the full voice-to-action pipeline:
from user input (voice/text) to intent classification, skill execution, and audio response generation.

---

## 📁 Project Structure

app/ → Entry points (CLI, WebSocket)

core/ → Core assistant logic & routing

services/ → LLM, STT, TTS, search, etc.

skills/ → Feature modules

api/ → FastAPI endpoints

database/ → DB models & repository

clients/ → External integrations (Ollama, Whisper)

tools/ → Model & patch utilities

tests/ → Test suite

docs/ → Documentation

---

## ⚙️ Installation

### 1. Clone repo

git clone https://github.com/KAlpAkbaba/jarvis-platform

cd jarvis-platform

### 2. Setup environment
python -m venv venv

venv\Scripts\activate   # Windows

pip install -r requirements.txt

###3. Configure environment

POSTGRES_DB=jarvis_db

POSTGRES_USER=postgres

POSTGRES_PASSWORD=your_password

OLLAMA_HOST=http://localhost:11434

🐳 Run with Docker
docker-compose up -d

Services:

PostgreSQL

SearXNG (local search engine)

▶️ Running the Assistant

CLI mode

python app/main.py

API mode

python api/server.py

Then open:

http://localhost:8000

🔎 Example Commands


"Yarın saat 2'de toplantı hatırlat"

"Tarkan çal"

"İstanbul hava durumu"

"Not al market alışverişi"

"Ankara'ya uçak bileti"

🧪 Testing


pytest tests/

🛠️ Technologies


Python

FastAPI

Ollama (LLM)

Whisper (STT)

Piper / XTTS (TTS)

PostgreSQL

SearXNG (self-hosted search)

Docker


📌 Roadmap


## 📌 Roadmap

✅ Completed

   -  [x] Real-time Speech-to-Text (Whisper Large v3, GPU)
   -  [x] Text-to-Speech (Piper TTS)
   -  [x] Local LLM intent classification (Ollama Qwen 2.5 7B)
   -  [x] Web search integration (SearXNG)
   -  [x] Notes & reminders system (PostgreSQL-backed)
   -  [x] Reservation workflows (Flight & Hotel via Playwright)
   -  [x] Weather information service
   -  [x] Web interface (FastAPI + ngrok)
   -  [x] Modular architecture (Jarvis Platform core)
   -  [x] Wake word detection (OpenWakeWord)
   -  [x] Context-aware conversation improvements
          
🚧 In Progress

   - [] IoT integration (Home Assistant support)
   - [] Personal profile & memory system
   - [] Proactive assistant behavior
   - [] Multi-language support (EN / TR / DE)
   - [] Face recognition / identity awareness

🎯 Future Vision
   - [] Fully offline, privacy-first AI assistant
   - [] Mobile companion application
   - [] Plugin ecosystem (3rd-party skills)
   - [] Real-time streaming voice interaction
   - [] Long-term memory & personalization engine

 ⚠️ Notes

 
Requires local model setup (Whisper, Ollama, TTS)

Some features depend on external services

Optimized for Turkish language use


👤 Author

Developed by Kadir Alp Akbaba
