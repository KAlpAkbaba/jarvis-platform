import os
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

CHARACTERS = {
    "jarvis": {
        "voice_id": "JBFqnCBsd6RMkjVDRZzb",
        "name": "George",
        "description": "Resmi, sicak, profesyonel"
    },
    "aria": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Sarah",
        "description": "Arkadascas, olgun, guven verici"
    },
    "robot": {
        "voice_id": None,
        "name": "Piper",
        "description": "Lokal, robot sesi"
    }
}

class ElevenLabsTTS:
    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)
        self.current_character = "jarvis"

    def set_character(self, character: str):
        if character in CHARACTERS:
            self.current_character = character
            return True
        return False

    def get_characters(self):
        return list(CHARACTERS.keys())

    def synthesize(self, text: str, character: str = None) -> bytes:
        char = character or self.current_character
        config = CHARACTERS.get(char, CHARACTERS["jarvis"])

        if config["voice_id"] is None:
            return None  # Piper kullan

        audio_gen = self.client.text_to_speech.convert(
            voice_id=config["voice_id"],
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.3,
                use_speaker_boost=True
            )
        )

        audio_bytes = b""
        for chunk in audio_gen:
            audio_bytes += chunk
        return audio_bytes
