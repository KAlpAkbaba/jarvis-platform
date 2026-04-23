# -*- coding: utf-8 -*-
from clients.piper_client import PiperClient
from core.config import config


class TTSService:
    def __init__(self):
        self.client = PiperClient(
            model_path=config.piper_model_path,
            length_scale=config.piper_length_scale,
        )

    def speak(self, text):
        if not text or not text.strip():
            return
        self.client.speak(text)
