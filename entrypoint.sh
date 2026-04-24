#!/bin/bash
# Ollama URL fix
sed -i 's/localhost:11434/172.17.0.1:11434/g' /app/clients/ollama_client.py
sed -i 's/localhost:5432/postgres:5432/g' /app/database/db.py
sed -i 's/localhost:5432/postgres:5432/g' /app/core/config.py
sed -i 's/localhost:8080/searxng:8080/g' /app/core/config.py
# DB tabloları oluştur
python3 -c "import sys; sys.path.insert(0,'/app'); from database.db import create_tables; create_tables()" 2>/dev/null || true
# Sunucu başlat
exec python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
