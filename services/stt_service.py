# -*- coding: utf-8 -*-
import numpy as np
import sounddevice as sd
import scipy.signal as signal
from clients.whisper_client import WhisperClient
from core.config import config


class STTService:
    def __init__(self):
        self.client = WhisperClient(model_id=config.whisper_model_id)
        self.silence_threshold = config.stt_silence_threshold
        self.device_id = config.stt_device_id
        self.sample_rate = int(sd.query_devices(self.device_id)['default_samplerate'])
        print(f"Mikrofon: ID={self.device_id}, {self.sample_rate} Hz")

    def record(self, seconds=None):
        seconds = seconds or config.stt_record_seconds
        print(f"\nDinliyorum... ({seconds} saniye)")
        recording = sd.rec(
            int(seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            device=self.device_id
        )
        sd.wait()
        print("Kayit tamamlandi, analiz ediliyor...")
        audio = recording.flatten()

        # Ses var mi kontrolu ham audio uzerinden yap
        if float(np.abs(audio).mean()) < self.silence_threshold:
            return None

        # Whisper icin 16000 Hz'e resample et
        if self.sample_rate != 16000:
            audio = signal.resample(audio, int(len(audio) * 16000 / self.sample_rate))

        return audio

    def transcribe(self, audio):
        return self.client.transcribe(audio, language=config.whisper_language)

    def listen(self, seconds=None):
        audio = self.record(seconds)
        if audio is None:
            return ""
        return self.transcribe(audio).strip()
