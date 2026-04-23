import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import warnings
warnings.filterwarnings("ignore")

import re
import time
import threading
import numpy as np
import sounddevice as sd
from datetime import datetime
from ses_tanıma import model as whisper_pipe, PROMPT
from ses_klonla import konuş
from llm_motor import llm_yanıt
from skills.web_arama import web_ara, hava_durumu_ara, haber_ara
from skills.medya import medya_komutu_işle, ses_ayarla, medyayı_durdur, netflix_aç, youtube_müzik_aç, youtube_aç
from skills.rezervasyon import rezervasyon_işle, diyalog_devam
from skills.hava_bildirimi import hava_bildirimi_baslat, hava_ayarla, hava_ayarları
import skills.rezervasyon as _rezervasyon_modulu
from ddgs import DDGS
from database import (konuşma_kaydet, not_ekle, notları_getir, notu_tamamla,
                      hatırlatıcıları_kontrol_et, zamani_gecen_notlari_arsivle,
                      gecmis_notlari_getir, zaman_ifadesi, notu_arsivle,
                      rezervasyonları_getir)

print("=" * 40)
print("   Yapay Zeka Asistan Başlatılıyor...")
print("=" * 40)

geçmiş = []


def komutu_işle(metin: str) -> str:
    global geçmiş
    if geçmiş is None:
        geçmiş = []
    metin_lower = metin.lower().strip()

    # --- Aktif rezervasyon diyalogu ---
    if _rezervasyon_modulu.diyalog_durumu.get("aktif"):
        return diyalog_devam(metin)

    # --- Ses kontrolü ---
    if any(k in metin_lower for k in ["sesi artır", "sesi aç", "sesi yükselt", "ses aç", "ses artır"]):
        return ses_ayarla("artır")
    if any(k in metin_lower for k in ["sesi azalt", "sesi kıs", "ses kıs", "ses azalt"]):
        return ses_ayarla("azalt")
    if any(k in metin_lower for k in ["sesi kapat", "sustur", "ses kapat"]):
        return ses_ayarla("kapat")
    if any(k in metin_lower for k in ["durdur", "devam et", "pause"]):
        return medyayı_durdur()

    # --- Netflix ---
    if "netflix" in metin_lower:
        temiz = metin_lower
        for k in ["netflix", "aç", "başlat", "çalıştır"]:
            temiz = temiz.replace(k, "").strip()
        return netflix_aç(temiz)

    # --- Müzik / YouTube ---
    if any(k in metin_lower for k in ["çal", "müzik çal", "şarkı çal", "youtube"]):
        temiz = metin_lower
        for k in ["çal", "müzik", "şarkı", "youtube", "aç", "oynat"]:
            temiz = temiz.replace(k, "").strip()
        return youtube_müzik_aç(temiz) if temiz else youtube_aç("müzik")

    # --- Hava bildirimi ---
    if any(k in metin_lower for k in ["sabah bildirimi", "hava bildirimi", "hava durumu bildirimi"]):
        saat_match = re.search(r'(\d{1,2})[:\.]?(\d{2})?', metin)
        if saat_match:
            saat = saat_match.group(1).zfill(2)
            dakika = saat_match.group(2) or "00"
            saat_str = f"{saat}:{dakika}"
            şehir = "İstanbul"
            for s in ["istanbul", "ankara", "izmir", "bursa", "antalya", "konya", "adana"]:
                if s in metin_lower:
                    şehir = s.capitalize()
                    break
            hava_ayarla(saat=saat_str, şehir=şehir, aktif=True)
            return f"Hava durumu bildirimi her sabah {saat_str}'de {şehir} için gelecek."
        for s in ["istanbul", "ankara", "izmir", "bursa", "antalya", "konya", "adana"]:
            if s in metin_lower:
                hava_ayarla(şehir=s.capitalize(), aktif=True)
                return f"Hava bildirimi {s.capitalize()} için ayarlandı. Saat: {hava_ayarları['saat']}."
        hava_ayarla(aktif=True)
        return f"Hava durumu bildirimi aktif. Her sabah {hava_ayarları['saat']}'de {hava_ayarları['şehir']} için."

    if any(k in metin_lower for k in ["hava bildirimini kapat", "sabah bildirimini kapat", "bildirimi kapat"]):
        hava_ayarla(aktif=False)
        return "Hava durumu bildirimi kapatıldı."

    # --- Notları göster ---
    if any(k in metin_lower for k in ["notlarım", "notları göster", "notlarımı", "notlar", "notları oku"]):
        notlar = notları_getir()
        if not notlar:
            return "Hiç notunuz yok."
        cevap = "Notlarınız. "
        for i, n in enumerate(notlar, 1):
            cevap += f"{i}. {n[1]}. "
        return cevap.strip()

    # --- Geçmiş notlar ---
    if any(k in metin_lower for k in ["geçmiş notlar", "eski notlar", "arşiv", "geçmiş hatırlatıcılar"]):
        notlar = gecmis_notlari_getir()
        if not notlar:
            return "Geçmiş notunuz yok."
        cevap = "Geçmiş notlarınız. "
        for i, n in enumerate(notlar, 1):
            zaman = zaman_ifadesi(n[2]) if n[2] else "zamanı belirsiz"
            cevap += f"{i}. {n[1]}, {zaman}. "
        return cevap.strip()

    # --- Hatırlatıcıları listele ---
    if any(k in metin_lower for k in ["hatırlatıcılarım", "hatırlatmalar", "planlarım", "planlarımı göster"]):
        notlar = notları_getir(kategori="hatırlatıcı")
        if not notlar:
            return "Planlanmış hatırlatıcınız yok."
        cevap = "Hatırlatıcılarınız. "
        for i, n in enumerate(notlar, 1):
            zaman = zaman_ifadesi(n[3]) if n[3] else "zamanı belirsiz"
            cevap += f"{i}. {n[1]}, {zaman}. "
        return cevap.strip()

    # --- Rezervasyonları listele ---
    if any(k in metin_lower for k in ["rezervasyonlarım", "rezervasyonları göster", "geçmiş rezervasyonlar"]):
        rezervasyonlar = rezervasyonları_getir()
        if not rezervasyonlar:
            return "Kayıtlı rezervasyonunuz yok."
        cevap = "Rezervasyonlarınız. "
        for i, r in enumerate(rezervasyonlar, 1):
            if r["tür"] == "otel":
                cevap += f"{i}. {r['şehir']} oteli, {r['giriş'].strftime('%d %B') if r['giriş'] else ''}. "
            elif r["tür"] == "uçak":
                cevap += f"{i}. {r['nereden']} {r['nereye']} uçuşu, {r['giriş'].strftime('%d %B') if r['giriş'] else ''}. "
        return cevap.strip()

    # --- Not sil ---
    if any(k in metin_lower for k in ["notu sil", "notu tamamla", "notu kaldır", "sil notu"]):
        notlar = notları_getir()
        if not notlar:
            return "Silinecek not bulunamadı."
        sayı = re.search(r'\d+', metin)
        if sayı:
            not_id = int(sayı.group())
            geçerli_idler = [n[0] for n in notlar]
            if not_id in geçerli_idler:
                notu_tamamla(not_id)
                return f"{not_id} numaralı notu sildim."
            else:
                return f"{not_id} numaralı not bulunamadı."
        if any(k in metin_lower for k in ["son notu", "son not", "sonuncuyu"]):
            son = notlar[-1]
            notu_tamamla(son[0])
            return f"Son notu sildim: {son[1]}"
        cevap = "Hangi notu silmek istiyorsunuz? "
        for i, n in enumerate(notlar, 1):
            cevap += f"{i}. {n[1]}. "
        return cevap.strip() + " Numara söyleyin."

    # --- LLM ---
    sonuç = llm_yanıt(metin, geçmiş)
    kategori = sonuç["kategori"]
    yanıt = sonuç["yanıt"]

    if kategori == "HATA":
        return yanıt if yanıt and "Hata:" not in yanıt else "Anlayamadım, tekrar söyler misiniz?"

    print(f"📂 Kategori: {kategori}")

    if kategori == "WEB_ARAMA":
        if any(k in metin_lower for k in ["hava", "sıcaklık", "yağmur", "derece"]):
            şehir = "İstanbul"
            for s in ["istanbul", "ankara", "izmir", "bursa", "antalya", "konya", "adana", "kıbrıs"]:
                if s in metin_lower:
                    şehir = s.capitalize()
            ham_sonuç = hava_durumu_ara(şehir)
        elif any(k in metin_lower for k in ["haber", "gündem", "son dakika"]):
            ham_sonuç = haber_ara(metin)
        else:
            ham_sonuç = web_ara(metin)

        özet_prompt = f"""Sen yardımcı bir Türkçe asistansın. Kullanıcı şunu sordu: "{metin}"

    Arama sonuçları:
    {ham_sonuç[:1000]}

    Görevin:
    - Soruyu doğrudan ve net cevapla
    - Önemli bilgileri (sayılar, tarihler, isimler) mutlaka ekle
    - 2-4 cümle yaz, ne çok kısa ne çok uzun
    - Web sitesi veya link önerme
    - Türkçe yaz, samimi ve akıcı ol
    - Eğer hava durumu sorduysa: sıcaklık, hissedilen, durum (bulutlu/açık/yağmurlu) mutlaka söyle
    - Eğer haber sorduysa: ne oldu, ne zaman, kim — kısaca özetle"""

        özet = llm_yanıt(özet_prompt)
        return özet["yanıt"] if özet["yanıt"] else "Bilgi bulunamadı."

    elif kategori == "MEDYA":
        medya_sorgu = sonuç.get("medya_sorgu") or metin
        return medya_komutu_işle(metin, medya_sorgu)

    elif kategori == "NOT_AL":
        içerik = sonuç.get("not_içerik") or metin
        not_ekle(içerik, kategori="genel")
        return f"Not kaydedildi: {içerik}"

    elif kategori == "HATIRLATICI":
        içerik = sonuç.get("not_içerik") or metin
        hatırlatma_str = sonuç.get("hatırlatma_zamanı")
        hatırlatma = None
        if hatırlatma_str:
            try:
                hatırlatma = datetime.strptime(hatırlatma_str, "%Y-%m-%d %H:%M")
            except:
                pass
        not_ekle(içerik, kategori="hatırlatıcı", hatırlatma=hatırlatma)
        if hatırlatma:
            zaman = zaman_ifadesi(hatırlatma)
            return f"Hatırlatıcı kaydedildi. {içerik}. {zaman}."
        return f"Hatırlatıcı kaydedildi: {içerik}"

    elif kategori == "REZERVASYON":
        detaylar = sonuç.get("rezervasyon_detay") or {}
        return rezervasyon_işle(metin, detaylar)

    elif kategori == "IOT":
        return yanıt

    else:
        return yanıt if yanıt else "Anlayamadım, tekrar söyler misiniz?"


def ses_var_mı(kayıt, eşik=0.01) -> bool:
    return float(np.abs(kayıt).mean()) > eşik


def hatırlatıcı_kontrol_döngüsü():
    bildirim_yapıldı = set()
    while True:
        try:
            hatırlatıcılar = hatırlatıcıları_kontrol_et()
            for not_id, içerik, hatırlatma in hatırlatıcılar:
                if not_id not in bildirim_yapıldı:
                    kalan = int((hatırlatma - datetime.now()).total_seconds() / 60)
                    mesaj = f"Hatırlatma: {kalan} dakika sonra {içerik}" if kalan > 0 else f"Hatırlatma: Şu an {içerik}"
                    print(f"\n⏰ {mesaj}")
                    konuş(mesaj)
                    bildirim_yapıldı.add(not_id)
            zamani_gecen_notlari_arsivle()
            if len(bildirim_yapıldı) > 100:
                bildirim_yapıldı.clear()
        except Exception as e:
            print(f"Hatırlatıcı hatası: {e}")
        time.sleep(60)


def hatırlatıcı_thread_baslat():
    thread = threading.Thread(target=hatırlatıcı_kontrol_döngüsü, daemon=True)
    thread.start()
    print("⏰ Hatırlatıcı sistemi başlatıldı!")


def main():
    global geçmiş
    hatırlatıcı_thread_baslat()
    hava_bildirimi_baslat(konuş)
    konuş("Merhaba! Asistan hazır, sizi dinliyorum.")
    print("\n✅ Asistan hazır! Konuşabilirsiniz.")
    print("Durdurmak için CTRL+C\n")

    while True:
        try:
            print(f"\n🎤 Dinliyorum... (5 saniye)")
            kayıt = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
            sd.wait()
            print("✓ Kayıt tamamlandı, analiz ediliyor...")

            if not ses_var_mı(kayıt):
                print("🔇 Sessizlik algılandı, atlıyorum...")
                continue

            audio = kayıt.flatten()
            result = whisper_pipe(
                audio,
                generate_kwargs={
                    "language": "turkish",
                    "task": "transcribe",
                }
            )
            metin = result["text"].strip()

            if not metin or len(metin) < 2:
                print("❌ Anlaşılır ses algılanamadı...")
                continue

            print(f"👤 Sen: {metin}")
            cevap = komutu_işle(metin)
            print(f"🤖 Asistan: {cevap}")
            konuş(cevap)

            konuşma_kaydet("user", metin)
            konuşma_kaydet("assistant", cevap)

            geçmiş.append({"role": "user", "content": metin})
            geçmiş.append({"role": "assistant", "content": cevap})
            if len(geçmiş) > 20:
                geçmiş = geçmiş[-20:]

        except KeyboardInterrupt:
            print("\n\nAsistan kapatılıyor...")
            konuş("Görüşmek üzere!")
            break
        except Exception as e:
            print(f"⚠️ Hata: {e}")
            time.sleep(1)
            continue


if __name__ == "__main__":
    main()