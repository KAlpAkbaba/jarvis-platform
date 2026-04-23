import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import warnings
warnings.filterwarnings("ignore")

import torch
import sounddevice as sd
import numpy as np
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

PROMPT = ""  # Artık kullanılmıyor ama main.py uyumluluğu için bırak

print("Whisper Large V3 yükleniyor (GPU)...")

_model = AutoModelForSpeechSeq2Seq.from_pretrained(
    "openai/whisper-large-v3",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    use_safetensors=True
).to("cuda")

_processor = AutoProcessor.from_pretrained("openai/whisper-large-v3")

model = pipeline(
    "automatic-speech-recognition",
    model=_model,
    tokenizer=_processor.tokenizer,
    feature_extractor=_processor.feature_extractor,
    torch_dtype=torch.float16,
    device="cuda",
)

print("Model hazır!")

def mikrofon_dinle(süre: int = 5) -> str:
    print(f"\n🎤 Dinliyorum... ({süre} saniye)")
    kayıt = sd.rec(int(süre * 16000), samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    print("✓ Kayıt tamamlandı, analiz ediliyor...")
    audio = kayıt.flatten()
    result = model(
        audio,
        generate_kwargs={
            "language": "turkish",
            "task": "transcribe",
        }
    )
    return result["text"].strip()