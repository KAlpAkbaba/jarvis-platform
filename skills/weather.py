import time
import threading
from datetime import datetime
from ddgs import DDGS
from llm_motor import llm_yanıt

# Ayarlar — kullanıcı sesli olarak değiştirebilir
hava_ayarları = {
    "aktif": False,
    "saat": "07:00",
    "şehir": "İstanbul"
}

def hava_durumu_özet(şehir: str) -> str:
    """DuckDuckGo'dan hava durumu çek ve özetle"""
    try:
        with DDGS() as ddgs:
            sonuçlar = list(ddgs.text(
                f"{şehir} hava durumu bugün sıcaklık yağmur min max hissedilen",
                region="tr-tr",
                max_results=3
            ))
        ham = "\n".join([s['body'] for s in sonuçlar[:3]])

        özet_prompt = f"""Aşağıdaki hava durumu bilgisini kullanarak {şehir} için kısa ve öz bir sabah bildirimi hazırla.
Şunları içersin: mevcut sıcaklık, hissedilen sıcaklık, günlük min/max, yağmur/kar uyarısı varsa belirt.
2-3 cümle, samimi ve günlük dilde konuş.

Hava verisi: {ham[:600]}"""

        sonuç = llm_yanıt(özet_prompt)
        return sonuç["yanıt"]
    except Exception as e:
        return f"{şehir} hava durumu alınamadı."

def hava_bildirimi_döngüsü(konuş_fn):
    """Arka planda çalışan hava bildirimi thread'i"""
    bildirim_yapıldı = set()

    while True:
        try:
            if hava_ayarları["aktif"]:
                şimdi = datetime.now()
                hedef = hava_ayarları["saat"]
                şimdi_str = şimdi.strftime("%H:%M")
                gün = şimdi.strftime("%Y-%m-%d")

                if şimdi_str == hedef and gün not in bildirim_yapıldı:
                    şehir = hava_ayarları["şehir"]
                    print(f"\n🌤️ Sabah hava durumu bildirimi: {şehir}")
                    özet = hava_durumu_özet(şehir)
                    print(f"🌤️ {özet}")
                    konuş_fn(f"Günaydın! {şehir} için bugünün hava durumu: {özet}")
                    bildirim_yapıldı.add(gün)

                # Eski günleri temizle
                if len(bildirim_yapıldı) > 7:
                    bildirim_yapıldı.clear()

        except Exception as e:
            print(f"Hava bildirimi hatası: {e}")

        time.sleep(30)  # Her 30 saniyede kontrol

def hava_bildirimi_baslat(konuş_fn):
    thread = threading.Thread(
        target=hava_bildirimi_döngüsü,
        args=(konuş_fn,),
        daemon=True
    )
    thread.start()
    print("🌤️ Hava durumu bildirimi sistemi başlatıldı!")

def hava_ayarla(saat: str = None, şehir: str = None, aktif: bool = None):
    """Hava bildirimi ayarlarını güncelle"""
    if saat:
        hava_ayarları["saat"] = saat
    if şehir:
        hava_ayarları["şehir"] = şehir
    if aktif is not None:
        hava_ayarları["aktif"] = aktif
    return hava_ayarları