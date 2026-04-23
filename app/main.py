# -*- coding: utf-8 -*-
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import warnings
warnings.filterwarnings("ignore")
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pyaudio
from core.assistant import Assistant
from services.reminder_service import ReminderService

WAKE_WORDS = ["jarvis", "jarvis orада misin", "jarvis orada misin", "orda misin", "merhaba jarvis"]
SLEEP_WORDS = ["dinlen", "sus", "bekle", "tamam dinlen"]
CHUNK = 1280
RATE = 16000
FORMAT = pyaudio.paInt16


def contains_wake_word(text):
    text_lower = text.lower().strip()
    return any(w in text_lower for w in WAKE_WORDS)

def contains_sleep_word(text):
    text_lower = text.lower().strip()
    return any(w in text_lower for w in SLEEP_WORDS)


def main():
    print("=" * 40)
    print("   Jarvis Platform Baslatiliyor...")
    print("=" * 40)

    assistant = Assistant()
    reminder_service = ReminderService(speak_fn=assistant.speak)
    reminder_service.start()
    assistant.weather.start()

    active = False
    print("\nPassif modda bekleniyor... ('Jarvis' deyin)")

    while True:
        try:
            if not active:
                # Pasif mod - kisa dinleme, wake word ara
                audio = assistant.stt.record(min_seconds=1, max_seconds=4, silence_duration=1.0)
                if audio is None:
                    continue
                text = assistant.stt.transcribe(audio).strip()
                if not text:
                    continue
                print(f"[Pasif] Algilandi: {text}")

                if contains_wake_word(text):
                    active = True
                    assistant.speak("Evet, buradayim!")
                    print("Aktif moda gecildi!")
                continue

            # Aktif mod - normal dinleme
            text = assistant.stt.listen()

            if not text or len(text) < 2:
                print("Sessizlik algilandi...")
                continue

            print(f"Sen: {text}")

            # Uyku komutu
            if contains_sleep_word(text):
                active = False
                assistant.speak("Tamam, dinleniyorum. Ihtiyaciniz olursa Jarvis deyin.")
                print("Pasif moda gecildi!")
                continue

            response = assistant.process(text)
            assistant.speak(response)
            assistant.update_history(text, response)

        except KeyboardInterrupt:
            print("\n\nAsistan kapatiliyor...")
            assistant.speak("Gorusmek uzere!")
            break
        except Exception as e:
            print(f"Hata: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
