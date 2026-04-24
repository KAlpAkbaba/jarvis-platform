import requests
from typing import List, Dict, Optional


OLLAMA_URL = 'http://172.17.0.1:11434/api/chat'
DEFAULT_MODEL = 'qwen2.5:7b'


class OllamaClient:
    def __init__(self, model=DEFAULT_MODEL, base_url=OLLAMA_URL):
        self.model = model
        self.base_url = base_url

    def chat(self, messages, num_predict=400, temperature=0.7,
             top_k=20, top_p=0.9, repeat_penalty=1.1, num_ctx=4096, timeout=30):
        try:
            response = requests.post(
                self.base_url,
                json={
                    'model': self.model,
                    'messages': messages,
                    'stream': False,
                    'options': {
                        'num_predict': num_predict,
                        'temperature': temperature,
                        'top_k': top_k,
                        'top_p': top_p,
                        'repeat_penalty': repeat_penalty,
                        'num_ctx': num_ctx,
                    },
                },
                timeout=timeout,
            )
            return response.json()['message']['content'].strip()
        except requests.exceptions.ConnectionError:
            raise ConnectionError('Ollama baglantisi kurulamadi.')
        except Exception as e:
            raise RuntimeError(f'Ollama hatasi: {e}')

    def is_available(self):
        try:
            requests.get('http://172.17.0.1:11434', timeout=3)
            return True
        except:
            return False
