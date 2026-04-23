import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import tempfile
import json
import base64
import soundfile as sf
import numpy as np

from llm_motor import llm_yanıt
from skills.web_arama import web_ara, hava_durumu_ara, haber_ara
from skills.medya import medya_komutu_işle
from database import konuşma_kaydet, not_ekle, notları_getir, notu_tamamla
from ddgs import DDGS

app = FastAPI()

# Modeller
print("Modeller yükleniyor...")
import whisper
whisper_model = whisper.load_model("medium", device="cpu")

from TTS.api import TTS
tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
BENIM_SESIM = "E:\\Project\\benim_sesim.wav"

print("Modeller hazır!")

geçmiş = []

def metni_işle(metin: str) -> str:
    """main.py'deki komutu_işle ile aynı mantık"""
    global geçmiş
    metin_lower = metin.lower().strip()

    if any(k in metin_lower for k in ["notlarım", "notları göster", "notlarımı", "notlar"]):
        notlar = notları_getir()
        if not notlar:
            return "Hiç notunuz yok."
        cevap = "Notlarınız. "
        for i, n in enumerate(notlar, 1):
            cevap += f"{i}. {n[1]}. "
        return cevap.strip()

    sonuç = llm_yanıt(metin, geçmiş)
    kategori = sonuç["kategori"]
    yanıt = sonuç["yanıt"]

    if kategori == "WEB_ARAMA":
        if any(k in metin_lower for k in ["hava", "sıcaklık", "derece"]):
            şehir = "İstanbul"
            for s in ["istanbul", "ankara", "izmir"]:
                if s in metin_lower:
                    şehir = s.capitalize()
            try:
                with DDGS() as ddgs:
                    sonuçlar = list(ddgs.text(f"{şehir} hava durumu şu an", region="tr-tr", max_results=3))
                ham = "\n".join([s['body'] for s in sonuçlar[:3]])
            except:
                ham = hava_durumu_ara(şehir)
        else:
            ham = web_ara(metin)
        özet = llm_yanıt(f'Kullanıcı sordu: "{metin}"\nSonuç: {ham[:600]}\n1-2 cümleyle Türkçe cevap ver.')
        return özet["yanıt"]

    elif kategori == "NOT_AL":
        içerik = sonuç.get("not_içerik") or metin
        not_ekle(içerik, kategori="genel")
        return f"Not kaydedildi: {içerik}"

    elif kategori == "HATIRLATICI":
        içerik = sonuç.get("not_içerik") or metin
        not_ekle(içerik, kategori="hatırlatıcı")
        return f"Hatırlatıcı kaydedildi: {içerik}"

    return yanıt if yanıt else "Anlayamadım, tekrar söyler misiniz?"

def ses_üret(metin: str) -> bytes:
    """Metni sese çevir ve bytes döndür"""
    metin = metin.replace('"', '').replace("'", '').replace('!', '.').replace('?', '.')
    cümleler = [c.strip() for c in metin.split(".") if len(c.strip()) > 2]

    tüm_ses = []
    sample_rate = 24000

    for cümle in cümleler:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            tts_model.tts_to_file(
                text=cümle,
                speaker_wav=BENIM_SESIM,
                language="tr",
                file_path=tmp.name,
                temperature=0.65,
                speed=0.95,
            )
            data, sr = sf.read(tmp.name)
            tüm_ses.extend(data.tolist())
            sample_rate = sr
            os.unlink(tmp.name)
        except:
            continue

    if not tüm_ses:
        return b""

    tmp2 = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp2.close()
    sf.write(tmp2.name, np.array(tüm_ses), sample_rate)
    with open(tmp2.name, "rb") as f:
        ses_bytes = f.read()
    os.unlink(tmp2.name)
    return ses_bytes

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global geçmiş

    try:
        while True:
            # Telefondan ses verisi al (base64)
            veri = await websocket.receive_text()
            mesaj = json.loads(veri)

            if mesaj["tip"] == "ses":
                # Base64 ses → numpy
                ses_bytes = base64.b64decode(mesaj["veri"])
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp.write(ses_bytes)
                tmp.close()

                # Whisper ile metne çevir
                result = whisper_model.transcribe(tmp.name, language="tr", fp16=False)
                metin = result["text"].strip()
                os.unlink(tmp.name)

                if not metin or len(metin) < 2:
                    await websocket.send_text(json.dumps({"tip": "hata", "mesaj": "Anlaşılamadı"}))
                    continue

                # Metni işle
                cevap = metni_işle(metin)

                # Konuşmayı kaydet
                konuşma_kaydet("user", metin)
                konuşma_kaydet("assistant", cevap)
                geçmiş.append({"role": "user", "content": metin})
                geçmiş.append({"role": "assistant", "content": cevap})
                if len(geçmiş) > 20:
                    geçmiş = geçmiş[-20:]

                # Ses üret
                ses = ses_üret(cevap)
                ses_b64 = base64.b64encode(ses).decode()

                await websocket.send_text(json.dumps({
                    "tip": "cevap",
                    "metin_kullanici": metin,
                    "metin_asistan": cevap,
                    "ses": ses_b64
                }))

            elif mesaj["tip"] == "metin":
                # Yazılı mesaj
                metin = mesaj["veri"]
                cevap = metni_işle(metin)
                ses = ses_üret(cevap)
                ses_b64 = base64.b64encode(ses).decode()
                await websocket.send_text(json.dumps({
                    "tip": "cevap",
                    "metin_kullanici": metin,
                    "metin_asistan": cevap,
                    "ses": ses_b64
                }))

    except Exception as e:
        print(f"WebSocket hatası: {e}")

@app.get("/")
async def ana_sayfa():
    return HTMLResponse(open("E:\\Project\\static\\index.html", encoding="utf-8").read())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)