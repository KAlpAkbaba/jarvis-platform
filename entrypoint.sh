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

# Outlook token yenile
python3 -c "
import requests, json, os
token_path = '/app/data/outlook_token.json'
if os.path.exists(token_path):
    try:
        with open(token_path) as f:
            data = json.load(f)
        refresh_token = data.get('refresh_token', '')
        if refresh_token:
            res = requests.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data={
                'client_id': '9b1ecc4d-c0cc-4123-8ec1-522c8f278ecf',
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'scope': 'Calendars.ReadWrite User.Read offline_access',
            })
            result = res.json()
            if 'access_token' in result:
                with open(token_path, 'w') as f:
                    json.dump(result, f)
                print('Outlook token yenilendi!')
    except Exception as e:
        print(f'Outlook token yenileme hatasi: {e}')
" 2>/dev/null || true
