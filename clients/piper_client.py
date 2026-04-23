# -*- coding: utf-8 -*-
import os
import wave
import io
import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
from piper.config import SynthesisConfig


class PiperClient:
    def __init__(self, model_path=r"E:\Project\tr_TR-dfki-medium.onnx", length_scale=0.8):
        self.model_path = model_path
        self.voice = None
        self.syn_config = None
        self._load(length_scale)

    def _load(self, length_scale):
        print("TTS modeli yukleniyor (Piper)...")
        self.voice = PiperVoice.load(self.model_path, use_cuda=False)
        self.syn_config = SynthesisConfig(length_scale=length_scale)
        print("TTS hazir!")

    def synthesize(self, text):
        text = text.replace('"', '').replace("'", '').replace('!', '.').replace('?', '.')
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 2]
        all_audio = []
        sample_rate = self.voice.config.sample_rate

        for sentence in sentences:
            try:
                buf = io.BytesIO()
                wf = wave.open(buf, 'wb')
                self.voice.synthesize_wav(sentence, wf, syn_config=self.syn_config)
                wf.close()
                buf.seek(0)
                with wave.open(buf, 'rb') as wav:
                    frames = wav.readframes(wav.getnframes())
                    sample_rate = wav.getframerate()
                if frames:
                    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    all_audio.extend(audio.tolist())
            except Exception as e:
                print(f"TTS hatasi: {e}")

        return np.array(all_audio), sample_rate

    def speak(self, text):
        audio, sr = self.synthesize(text)
        if len(audio) > 0:
            sd.play(audio, sr)
            sd.wait()
