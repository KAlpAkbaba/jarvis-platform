import requests
import json
import re
from datetime import datetime, timedelta

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"


def sistem_prompt_olustur() -> str:
    şimdi = datetime.now()
    bugun = şimdi.strftime("%Y-%m-%d")
    saat = şimdi.strftime("%H:%M")
    yarın = (şimdi + timedelta(days=1)).strftime("%Y-%m-%d")
    obur_gun = (şimdi + timedelta(days=2)).strftime("%Y-%m-%d")

    return f"""Sen Türkçe konuşan zeki bir yapay zeka asistanısın.
Bugünün tarihi: {bugun}, şu anki saat: {saat}
Yarının tarihi: {yarın}
Öbür günün tarihi: {obur_gun}

Kullanıcının mesajını analiz et ve SADECE şu JSON formatında yanıt ver:

{{
    "kategori": "WEB_ARAMA|MEDYA|REZERVASYON|NOT_AL|HATIRLATICI|IOT|SOHBET",
    "yanıt": "kullanıcıya verilecek kısa Türkçe cevap (HER ZAMAN dolu olmalı)",
    "not_içerik": "eğer NOT_AL veya HATIRLATICI ise sadece not içeriği, değilse null",
    "hatırlatma_zamanı": "eğer HATIRLATICI ise 'YYYY-MM-DD HH:MM' formatında TAM TARİH, değilse null",
    "medya_sorgu": "eğer MEDYA ise aranacak şarkı/video adı, değilse null",
    "rezervasyon_detay": {{
        "tür": "otel veya uçak veya restoran veya null",
        "şehir": "şehir adı veya null",
        "nereden": "kalkış şehri veya null",
        "nereye": "varış şehri veya null",
        "tarih": "YYYY-MM-DD veya null",
        "giriş_tarihi": "YYYY-MM-DD veya null",
        "çıkış_tarihi": "YYYY-MM-DD veya null",
        "kişi": 1
    }}
}}

KATEGORİ KURALLARI:
- NOT_AL: Sadece "not al", "kaydet", "yaz" dediğinde
- HATIRLATICI: "hatırlat", "alarm", "unutma", "gerekiyor" gibi kelimeler varsa
- WEB_ARAMA: Bilgi soruları, "nedir", "kaç", "hava", "haber"
- MEDYA: "çal", "aç", "oynat", "müzik", "film"
- REZERVASYON: "rezervasyon", "otel", "uçak", "bilet", "restoran", "yer ayırt" gibi kelimeler varsa
- SOHBET: Selam, nasılsın, fıkra, genel konuşma

TARİH HESAPLAMA (bugün {bugun}):
- "bugün" → {bugun}
- "yarın" → {yarın}
- "öbür gün" → {obur_gun}
- "saat iki" veya "saat ikide" → 14:00
- "saat üç" veya "saat üçte" → 15:00
- "saat on iki" veya "öğlen" → 12:00
- "akşam" → 19:00
- "sabah" → 09:00
- "12-15" veya "12.15" → 12:15
- "14-30" veya "14.30" → 14:30

NOT İÇERİK KURALLARI:
- "hatırlat", "not al", "kaydet", "lütfen", "gerekiyor", "lazım" gibi komut kelimelerini çıkar
- Sadece asıl içeriği kısa ve öz yaz

REZERVASYON KURALLARI:
- "İstanbul'da otel ara" → tür: otel, şehir: İstanbul
- "Ankara'ya uçak" → tür: uçak, nereden: İstanbul (varsayılan), nereye: Ankara
- "Yarın akşam restoran" → tür: restoran, tarih: {yarın}
- Kişi sayısı belirtilmezse 1 yaz
- Tarih belirtilmezse null yaz

GENEL ÖRNEKLER:
- "Yarın saat 2de toplantı hatırlat" → {{"kategori":"HATIRLATICI","yanıt":"Hatırlatıcı kaydedildi.","not_içerik":"Toplantı","hatırlatma_zamanı":"{yarın} 14:00","medya_sorgu":null,"rezervasyon_detay":null}}
- "Not al market alışverişi" → {{"kategori":"NOT_AL","yanıt":"Notunuzu kaydettim.","not_içerik":"market alışverişi","hatırlatma_zamanı":null,"medya_sorgu":null,"rezervasyon_detay":null}}
- "Tarkan çal" → {{"kategori":"MEDYA","yanıt":"Tarkan çalıyor.","not_içerik":null,"hatırlatma_zamanı":null,"medya_sorgu":"Tarkan","rezervasyon_detay":null}}
- "İstanbul'da 3 gecelik otel ara" → {{"kategori":"REZERVASYON","yanıt":"İstanbul otelleri aranıyor.","not_içerik":null,"hatırlatma_zamanı":null,"medya_sorgu":null,"rezervasyon_detay":{{"tür":"otel","şehir":"İstanbul","nereden":null,"nereye":null,"tarih":null,"giriş_tarihi":null,"çıkış_tarihi":null,"kişi":1}}}}
- "Ankara'ya uçak bileti" → {{"kategori":"REZERVASYON","yanıt":"Ankara uçuşları aranıyor.","not_içerik":null,"hatırlatma_zamanı":null,"medya_sorgu":null,"rezervasyon_detay":{{"tür":"uçak","şehir":null,"nereden":"İstanbul","nereye":"Ankara","tarih":null,"giriş_tarihi":null,"çıkış_tarihi":null,"kişi":1}}}}
- "Nasılsın" → {{"kategori":"SOHBET","yanıt":"İyiyim, sen?","not_içerik":null,"hatırlatma_zamanı":null,"medya_sorgu":null,"rezervasyon_detay":null}}

Sadece JSON döndür. yanıt alanı HİÇBİR ZAMAN boş olamaz."""


def llm_yanıt(kullanıcı_mesajı: str, geçmiş: list = []) -> dict:
    sistem = sistem_prompt_olustur()

    mesajlar = [{"role": "system", "content": sistem}]
    mesajlar.extend(geçmiş)
    mesajlar.append({"role": "user", "content": kullanıcı_mesajı})

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": mesajlar,
                "stream": False,
                "options": {
                    "num_predict": 400,  # 200'den 400'e çıkar
                    "temperature": 0.7,
                    "top_k": 20,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "num_ctx": 4096  # 2048'den 4096'ya çıkar
                }
            },
            timeout=30
        )

        yanıt_metni = response.json()["message"]["content"].strip()
        yanıt_metni = re.sub(r"```json|```", "", yanıt_metni).strip()

        json_match = re.search(r'\{.*\}', yanıt_metni, re.DOTALL)
        if json_match:
            yanıt_metni = json_match.group()

        veri = json.loads(yanıt_metni)

        return {
            "kategori": veri.get("kategori", "SOHBET"),
            "yanıt": veri.get("yanıt") or "Anlıyorum.",
            "not_içerik": veri.get("not_içerik", None),
            "hatırlatma_zamanı": veri.get("hatırlatma_zamanı", None),
            "medya_sorgu": veri.get("medya_sorgu", None),
            "rezervasyon_detay": veri.get("rezervasyon_detay", None),
            "ham": yanıt_metni
        }

    except requests.exceptions.ConnectionError:
        return {
            "kategori": "HATA",
            "yanıt": "Ollama bağlantısı kurulamadı.",
            "not_içerik": None,
            "hatırlatma_zamanı": None,
            "medya_sorgu": None,
            "rezervasyon_detay": None,
            "ham": ""
        }
    except json.JSONDecodeError:
        try:
            response2 = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Sen yardımcı bir Türkçe asistansın. Kısa ve net cevap ver."},
                        {"role": "user", "content": kullanıcı_mesajı}
                    ],
                    "stream": False
                },
                timeout=30
            )
            düz_yanıt = response2.json()["message"]["content"].strip()
            return {
                "kategori": "SOHBET",
                "yanıt": düz_yanıt[:300],
                "not_içerik": None,
                "hatırlatma_zamanı": None,
                "medya_sorgu": None,
                "rezervasyon_detay": None,
                "ham": düz_yanıt
            }
        except:
            return {
                "kategori": "SOHBET",
                "yanıt": "Şu an düşünüyorum, tekrar sorar mısınız?",
                "not_içerik": None,
                "hatırlatma_zamanı": None,
                "medya_sorgu": None,
                "rezervasyon_detay": None,
                "ham": ""
            }
    except Exception as e:
        return {
            "kategori": "HATA",
            "yanıt": f"Hata: {str(e)}",
            "not_içerik": None,
            "hatırlatma_zamanı": None,
            "medya_sorgu": None,
            "rezervasyon_detay": None,
            "ham": ""
        }


if __name__ == "__main__":
    testler = [
        "İstanbul'da 2 gecelik otel ara",
        "Ankara'ya yarın uçak bileti",
        "Yarın akşam 2 kişilik restoran rezervasyonu",
        "Yarın saat 2de toplantım var hatırlat",
        "Not al market alışverişi",
        "Tarkan çal",
        "Nasılsın",
    ]

    for test in testler:
        print(f"\n👤 {test}")
        sonuç = llm_yanıt(test)
        print(f"📂 Kategori: {sonuç['kategori']}")
        print(f"🤖 Yanıt: {sonuç['yanıt']}")
        if sonuç['not_içerik']:
            print(f"📝 Not: {sonuç['not_içerik']}")
        if sonuç['hatırlatma_zamanı']:
            print(f"⏰ Zaman: {sonuç['hatırlatma_zamanı']}")
        if sonuç['rezervasyon_detay']:
            print(f"🏨 Rezervasyon: {sonuç['rezervasyon_detay']}")

