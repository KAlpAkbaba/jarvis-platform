content = """# -*- coding: utf-8 -*-

class TTSService:
    def __init__(self):
        self.client = None
        print("TTS: Sunucu modunda ses cikisi devre disi.")

    def speak(self, text: str):
        # Sunucuda ses cikisi yok - client tarafinda yapilacak
        print(f"TTS [server]: {text}")

    def synthesize(self, text: str):
        return None, None
"""
with open('services/tts_service.py', 'w') as f:
    f.write(content)
print('tts_service.py guncellendi!')
