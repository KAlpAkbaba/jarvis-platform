with open('api/server.py', 'r') as f:
    content = f.read()

cors = """from fastapi.middleware.cors import CORSMiddleware\n"""
middleware = """
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

if 'CORSMiddleware' not in content:
    content = cors + content
    content = content.replace(
        'app = FastAPI(',
        'app = FastAPI('
    )
    idx = content.find('\n\n@app')
    content = content[:idx] + middleware + content[idx:]
    with open('api/server.py', 'w') as f:
        f.write(content)
    print('CORS eklendi!')
else:
    print('CORS zaten mevcut.')
