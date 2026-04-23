import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import warnings

warnings.filterwarnings("ignore")

import wave
import io
import sounddevice as sd
import numpy as np
from piper.voice import PiperVoice
from piper.config import SynthesisConfig

print("TTS modeli yükleniyor (Piper)...")
voice = PiperVoice.load(
    r"E:\Project\tr_TR-dfki-medium.onnx",
    use_cuda=False
)
syn_config = SynthesisConfig(length_scale=0.8)
print("TTS hazır!")


def konuş(metin: str):
    metin = metin.replace('"', '').replace("'", '')
    metin = metin.replace('!', '.').replace('?', '.')

    cümleler = [c.strip() for c in metin.split(".") if len(c.strip()) > 2]
    if not cümleler:
        return

    tüm_ses = []
    sample_rate = 22050

    for cümle in cümleler:
        try:
            buf = io.BytesIO()
            wav_file = wave.open(buf, "wb")
            voice.synthesize_wav(cümle, wav_file, syn_config=syn_config)
            wav_file.close()

            buf.seek(0)
            with wave.open(buf, "rb") as wav:
                frames = wav.readframes(wav.getnframes())
                sample_rate = wav.getframerate()

            if frames:
                ses = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                tüm_ses.extend(ses.tolist())
        except Exception as e:
            print(f"⚠️ TTS hatası: {e}")
            continue

    if tüm_ses:
        sd.play(np.array(tüm_ses), sample_rate)
        sd.wait()


if __name__ == "__main__":
    import time

    t = time.time()
    konuş("Merhaba! Piper TTS ile konuşuyorum. Çok daha hızlı değil mi?")
    print(f"⚡ TTS süresi: {time.time() - t:.2f}s")

