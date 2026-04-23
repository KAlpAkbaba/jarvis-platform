import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.assistant import Assistant
from services.reminder_service import ReminderService


def main():
    print("=" * 40)
    print("   Jarvis Platform Baslatiliyor...")
    print("=" * 40)

    assistant = Assistant()

    reminder_service = ReminderService(speak_fn=assistant.speak)
    reminder_service.start()

    assistant.weather.start()

    assistant.speak("Merhaba! Asistan hazir, sizi dinliyorum.")
    print("\nAsistan hazir! Konusabilirsiniz.")
    print("Durdurmak icin CTRL+C\n")

    while True:
        try:
            text = assistant.stt.listen()

            if not text or len(text) < 2:
                print("Sessizlik algilandi...")
                continue

            print(f"Sen: {text}")
            response = assistant.process(text)
            assistant.speak(response)
            assistant.update_history(text, response)

        except KeyboardInterrupt:
            print("\n\nAsistan kapatiliyor...")
            assistant.speak("Gorusmek uzere!")
            break
        except Exception as e:
            print(f"Hata: {e}")


if __name__ == "__main__":
    main()
