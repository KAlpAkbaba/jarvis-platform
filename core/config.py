import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(r'E:\Project')

@dataclass
class Config:
    ollama_url: str = 'http://localhost:11434/api/chat'
    llm_model: str = 'qwen2.5:7b'
    llm_num_predict: int = 400
    llm_temperature: float = 0.7
    llm_top_k: int = 20
    llm_top_p: float = 0.9
    llm_repeat_penalty: float = 1.1
    llm_num_ctx: int = 4096
    whisper_model_id: str = 'openai/whisper-large-v3'
    whisper_language: str = 'turkish'
    stt_record_seconds: int = 5
    stt_sample_rate: int = 16000
    stt_silence_threshold: float = 0.01
    piper_model_path: str = str(BASE_DIR / 'tr_TR-dfki-medium.onnx')
    piper_length_scale: float = 0.8
    db_url: str = 'postgresql://postgres:***REMOVED***@localhost:5432/asistan'
    searxng_url: str = 'http://localhost:8080/search'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    chromedriver_path: str = str(BASE_DIR / 'chromedriver.exe')
    weather_city: str = 'Istanbul'
    weather_time: str = '07:00'
    weather_enabled: bool = False

    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            llm_model=os.getenv('LLM_MODEL', 'qwen2.5:7b'),
            db_url=os.getenv('DATABASE_URL', 'postgresql://postgres:***REMOVED***@localhost:5432/asistan'),
            searxng_url=os.getenv('SEARXNG_URL', 'http://localhost:8080/search'),
            weather_city=os.getenv('WEATHER_CITY', 'Istanbul'),
        )

config = Config()


