import sys
sys.path.insert(0, r'E:\jarvis-platform')

new_stt = '''# -*- coding: utf-8 -*-
import numpy as np
# import sounddevice as sd
import scipy.signal as signal
from collections import deque
from clients.whisper_client import WhisperClient
from core.config import config


class STTService:
    def __init__(self):
        self.client = WhisperClient(model_id=config.whisper_model_id)
        self.silence_threshold = config.stt_silence_threshold
        self.device_id = config.stt_device_id
        self.sample_rate = int(sd.query_devices(self.device_id)["default_samplerate"])
        print(f"Mikrofon: ID={self.device_id}, {self.sample_rate} Hz")

    def record(self, min_seconds=1, max_seconds=15, silence_duration=1.5):
        chunk_size = int(self.sample_rate * 0.1)
        silence_chunks = int(silence_duration / 0.1)
        min_chunks = int(min_seconds / 0.1)
        max_chunks = int(max_seconds / 0.1)

        print("\\nDinliyorum...")
        all_audio = []
        silent_count = 0
        speaking_started = False
        chunk_count = 0

        with sd.InputStream(samplerate=self.sample_rate, channels=1,
                            dtype="float32", device=self.device_id,
                            blocksize=chunk_size) as stream:
            while chunk_count < max_chunks:
                chunk, _ = stream.read(chunk_size)
                audio_chunk = chunk.flatten()
                level = float(np.abs(audio_chunk).mean())
                all_audio.extend(audio_chunk.tolist())
                chunk_count += 1

                if level > self.silence_threshold:
                    speaking_started = True
                    silent_count = 0
                else:
                    if speaking_started:
                        silent_count += 1

                if speaking_started and silent_count >= silence_chunks and chunk_count >= min_chunks:
                    break

        print("Kayit tamamlandi, analiz ediliyor...")
        audio = np.array(all_audio)

        if not speaking_started or float(np.abs(audio).mean()) < self.silence_threshold:
            return None

        if self.sample_rate != 16000:
            audio = signal.resample(audio, int(len(audio) * 16000 / self.sample_rate))

        return audio

    def transcribe(self, audio):
        return self.client.transcribe(audio, language=config.whisper_language)

    def listen(self):
        audio = self.record()
        if audio is None:
            return ""
        return self.transcribe(audio).strip()
'''

with open("services/stt_service.py", "w", encoding="utf-8") as f:
    f.write(new_stt)
print("stt_service.py guncellendi!")
