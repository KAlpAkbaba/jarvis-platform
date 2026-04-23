import asyncio
import re
import json
import time
from urllib.parse import quote
from datetime import datetime
from playwright.async_api import async_playwright

diyalog_durumu = {
    "aktif": False,
    "adım": None,
    "veri": {}
}

HAVALİMANI_KODLARI = {
    "istanbul": "IST",
    "ankara": "ESB",
    "izmir": "ADB",
    "antalya": "AYT",
    "bursa": "BTZ",
    "trabzon": "TZX",
    "adana": "ADA",
    "kıbrıs": "ECN",
    "lefkoşa": "ECN",
    "gazimağusa": "ECN",
    "larnaka": "LCA",
    "bodrum": "BJV",
    "dalaman": "DLM",
    "kayseri": "ASR",
    "samsun": "SZF",
    "erzurum": "ERZ",
    "diyarbakır": "DIY",
    "sabiha": "SAW",
}

SLUG = {
    "IST": "istanbul-ataturk-havalimani-ista-ist",
    "SAW": "istanbul-sabiha-gokcen-havalimani-ista-saw",
    "ESB": "ankara-ankara-esenboga-havalimani-ista-esb",
    "ADB": "izmir-adnan-menderes-havalimani-ista-adb",
    "AYT": "antalya-antalya-havalimani-ista-ayt",
    "ECN": "ecn-ercan-intl-havalimani-ista-ecn",
    "LCA": "larnaka-larnaka-intl-havalimani-ista-lca",
    "BJV": "bodrum-milas-bodrum-havalimani-ista-bjv",
    "DLM": "dalaman-dalaman-havalimani-ista-dlm",
    "TZX": "trabzon-trabzon-havalimani-ista-tzx",
    "ADA": "adana-adana-havalimani-ista-ada",
    "ASR": "kayseri-erkilet-havalimani-ista-asr",
}

YURT_DISI = {"ECN", "LCA"}


def slug_temizle(metin: str) -> str:
    çeviri = {
        'ı': 'i', 'İ': 'i', 'ğ': 'g', 'Ğ': 'g',
        'ü': 'u', 'Ü': 'u', 'ş': 's', 'Ş': 's',
        'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }
    for tr, en in çeviri.items():
        metin = metin.replace(tr, en)
    return metin.lower()


def şehir_kodu(şehir: str) -> str:
    if not şehir:
        return "IST"
    şehir_temiz = şehir.replace('İ', 'i').replace('I', 'i').lower()
    return HAVALİMANI_KODLARI.get(şehir_temiz, şehir.upper()[:3])


def sync_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except:
        return asyncio.run(coro)


def puan_sayıya_çevir(puan_str):
    try:
        temiz = ""
        for c in puan_str:
            if c.isdigit() or c in ".,":
                temiz += c
        if temiz:
            return float(temiz.replace(",", "."))
    except:
        pass
    return 0.0


# ============ OTEL ============

async def _booking_ara_async(şehir: str, giriş: str, çıkış: str, kişi: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = (
            f"https://www.booking.com/searchresults.tr.html"
            f"?ss={quote(şehir, encoding='utf-8')}"
            f"&checkin={giriş}&checkout={çıkış}"
            f"&group_adults={kişi}&no_rooms=1"
            f"&selected_currency=TRY&order=class"
        )

        await page.goto(url)
        await page.wait_for_timeout(4000)

        for selector in ['[aria-label="Kapat"]', '[aria-label="Close"]', '[data-testid="modal-close-button"]']:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(500)
                    break
            except:
                continue

        oteller = []
        kartlar = await page.query_selector_all('[data-testid="property-card"]')

        for kart in kartlar[:5]:
            try:
                ad_el = await kart.query_selector('[data-testid="title"]')
                fiyat_el = await kart.query_selector('[data-testid="price-and-discounted-price"]')
                puan_el = await kart.query_selector('[data-testid="review-score"]')
                link_el = await kart.query_selector('a[data-testid="title-link"]')

                ad = await ad_el.inner_text() if ad_el else ""
                fiyat = await fiyat_el.inner_text() if fiyat_el else "Fiyat yok"
                puan_metin = await puan_el.inner_text() if puan_el else "-"
                link = await link_el.get_attribute("href") if link_el else ""

                rakam = re.search(r'[\d,\.]+', puan_metin)
                puan = rakam.group() if rakam else "-"

                if ad:
                    oteller.append({
                        "ad": ad.strip(),
                        "fiyat": fiyat.strip(),
                        "puan": puan,
                        "kaynak": "Booking.com",
                        "link": link
                    })
            except:
                continue

        await browser.close()
        return oteller


def otelleri_karşılaştır(şehir: str, giriş: str, çıkış: str, kişi: int):
    print(f"🔍 {şehir} otelleri araştırılıyor...")
    oteller = sync_run(_booking_ara_async(şehir, giriş, çıkış, kişi))

    if not oteller:
        return f"{şehir} için Booking.com açıldı. Ekrandan oteli seçip numarasını söyleyin."

    oteller.sort(key=lambda x: puan_sayıya_çevir(x["puan"]), reverse=True)

    cevap = f"{şehir} için en iyi oteller. "
    for i, otel in enumerate(oteller[:3], 1):
        cevap += f"{i}. {otel['ad']}, fiyat {otel['fiyat']}, puan {otel['puan']}. "
    cevap += "Hangisini tercih edersiniz? Numara söyleyin."

    return cevap, oteller


# ============ UÇAK ============

async def _enuygun_ara_async(nereden_slug: str, nereye_slug: str, tarih_format: str, yolcu: int, geotrip: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = (
            f"https://www.enuygun.com/ucak-bileti/arama/"
            f"{nereden_slug}-{nereye_slug}/"
            f"?gidis={tarih_format}&yetiskin={yolcu}"
            f"&sinif=ekonomi&save=1&geotrip={geotrip}&trip={geotrip}"
        )

        print(f"Enuygun URL: {url}")
        await page.goto(url)
        await page.wait_for_timeout(6000)

        for selector in ['#CybotCookiebotDialogBodyButtonAccept', 'button:has-text("KABUL ET")']:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue

        uçuşlar = []
        for selector in ['.flight-card', '[data-testid="flight-card"]', '.result-item']:
            kartlar = await page.query_selector_all(selector)
            if kartlar:
                for kart in kartlar[:5]:
                    try:
                        havayolu_el = await kart.query_selector('.airline-name, [class*="airline"]')
                        fiyat_el = await kart.query_selector('.price, [class*="price"]')
                        havayolu = await havayolu_el.inner_text() if havayolu_el else "?"
                        fiyat = await fiyat_el.inner_text() if fiyat_el else "?"
                        uçuşlar.append({
                            "havayolu": havayolu,
                            "fiyat": fiyat,
                            "saat": "",
                            "kaynak": "Enuygun.com"
                        })
                    except:
                        continue
                break

        await browser.close()
        return uçuşlar


def enuygun_ara(nereden: str, nereye: str, tarih: str, yolcu: int) -> list:
    nereden = nereden.replace("(varsayılan)", "").replace("varsayılan", "").strip()
    nereye = nereye.replace("(varsayılan)", "").replace("varsayılan", "").strip()
    if not nereden:
        nereden = "Istanbul"

    nereden_kodu = şehir_kodu(nereden)
    nereye_kodu = şehir_kodu(nereye)

    tarih_obj = datetime.strptime(tarih, "%Y-%m-%d")
    tarih_format = tarih_obj.strftime("%d.%m.%Y")

    nereden_slug = SLUG.get(nereden_kodu, slug_temizle(nereden) + "-ista-" + nereden_kodu.lower())
    nereye_slug = SLUG.get(nereye_kodu, slug_temizle(nereye) + "-ista-" + nereye_kodu.lower())

    geotrip = "international" if nereden_kodu in YURT_DISI or nereye_kodu in YURT_DISI else "domestic"

    return sync_run(_enuygun_ara_async(nereden_slug, nereye_slug, tarih_format, yolcu, geotrip))


def uçakları_karşılaştır(nereden: str, nereye: str, tarih: str, yolcu: int):
    print(f"✈️ {nereden} → {nereye} uçuşları araştırılıyor...")
    uçuşlar = enuygun_ara(nereden, nereye, tarih, yolcu)

    if not uçuşlar:
        nereden_kodu = şehir_kodu(nereden)
        nereye_kodu = şehir_kodu(nereye)
        tarih_obj = datetime.strptime(tarih, "%Y-%m-%d")
        tarih_format = tarih_obj.strftime("%d.%m.%Y")
        nereden_slug = SLUG.get(nereden_kodu, slug_temizle(nereden) + "-ista-" + nereden_kodu.lower())
        nereye_slug = SLUG.get(nereye_kodu, slug_temizle(nereye) + "-ista-" + nereye_kodu.lower())
        geotrip = "international" if nereden_kodu in YURT_DISI or nereye_kodu in YURT_DISI else "domestic"
        sync_run(_enuygun_ara_async(nereden_slug, nereye_slug, tarih_format, yolcu, geotrip))
        return f"{nereden} → {nereye} için {tarih} tarihli uçuşlar Enuygun.com'da listelendi."

    uçuşlar.sort(key=lambda x: x["fiyat"])
    cevap = f"{nereden} → {nereye} için {tarih} tarihli en uygun uçuşlar. "
    for i, uçuş in enumerate(uçuşlar[:3], 1):
        cevap += f"{i}. {uçuş['havayolu']}, fiyat {uçuş['fiyat']}. "
    cevap += "Hangisini tercih edersiniz?"
    return cevap, uçuşlar


# ============ YARDIMCI ============

def tarih_parse(metin: str) -> str:
    metin = metin.lower().strip()
    şimdi = datetime.now()
    yıl = şimdi.year

    aylar = {
        "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4,
        "mayıs": 5, "haziran": 6, "temmuz": 7, "ağustos": 8,
        "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12,
        "mais": 5, "maiz": 5, "mayız": 5, "mays": 5,
        "hazran": 6, "temmüz": 7,
    }

    sayılar = {
        "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5,
        "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10,
        "on bir": 11, "on iki": 12, "on üç": 13, "on dört": 14,
        "on beş": 15, "on altı": 16, "on yedi": 17, "on sekiz": 18,
        "on dokuz": 19, "yirmi": 20, "yirmi bir": 21, "yirmi iki": 22,
        "yirmi üç": 23, "yirmi dört": 24, "yirmi beş": 25,
        "yirmi altı": 26, "yirmi yedi": 27, "yirmi sekiz": 28,
        "yirmi dokuz": 29, "otuz": 30, "otuz bir": 31,
        "pir": 1, "üc": 3, "uc": 3,
    }

    direkt = re.search(r'(\d{4})-(\d{2})-(\d{2})', metin)
    if direkt:
        return direkt.group()

    ay = None
    for ay_adı, ay_no in sorted(aylar.items(), key=lambda x: -len(x[0])):
        if ay_adı in metin:
            ay = ay_no
            metin = metin.replace(ay_adı, "").strip()
            break

    gün = None
    rakam = re.search(r'\b(\d{1,2})\b', metin)
    if rakam:
        gün = int(rakam.group(1))
    else:
        for sözel, rakam_val in sorted(sayılar.items(), key=lambda x: -len(x[0])):
            if sözel in metin:
                gün = rakam_val
                break

    if gün and ay:
        try:
            tarih = datetime(yıl, ay, gün)
            if tarih < şimdi:
                tarih = datetime(yıl + 1, ay, gün)
            return tarih.strftime("%Y-%m-%d")
        except:
            return None

    return None


def sözel_sayı_parse(metin: str) -> int:
    sözel_sayılar = {
        "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5,
        "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10,
        "pir": 1, "uc": 3, "üc": 3
    }
    metin_lower = metin.lower()
    sayı = re.search(r'\d+', metin)
    if sayı:
        return int(sayı.group())
    for sözel, rakam in sözel_sayılar.items():
        if sözel in metin_lower:
            return rakam
    return 1


# ============ DİYALOG ============

def rezervasyon_diyalogu(metin: str, detaylar: dict, geçmiş_rezervasyonlar: list = []) -> str:
    global diyalog_durumu
    metin_lower = metin.lower()
    tür = detaylar.get("tür", "") if detaylar else ""

    if any(k in metin_lower for k in ["geçen", "önceki", "yaptığın", "bulduğun"]):
        for rez in geçmiş_rezervasyonlar:
            if rez["tür"] == "otel" and "uçak" in metin_lower:
                return (
                    f"Geçmiş otel rezervasyonunuzu buldum: {rez['şehir']} için "
                    f"{rez['giriş'].strftime('%d %B') if rez['giriş'] else ''}. "
                    f"Bu tarihe uygun uçak aramalı mıyım?"
                )

    if tür == "otel" or any(k in metin_lower for k in ["otel", "konaklama"]):
        şehir = detaylar.get("şehir") if detaylar else None
        giriş = detaylar.get("giriş_tarihi") if detaylar else None
        çıkış = detaylar.get("çıkış_tarihi") if detaylar else None
        kişi = detaylar.get("kişi", 2) if detaylar else 2

        if not şehir:
            diyalog_durumu = {"aktif": True, "adım": "otel_şehir", "veri": {}}
            return "Hangi şehirde otel arayayım?"

        diyalog_durumu = {
            "aktif": True, "adım": "otel_şehir_onay",
            "veri": {"şehir": şehir, "giriş": giriş, "çıkış": çıkış, "kişi": kişi}
        }
        return f"{şehir} için otel arayayım, doğru mu?"

    elif tür == "uçak" or any(k in metin_lower for k in ["uçak", "uçuş", "bilet"]):
        nereden = detaylar.get("nereden") if detaylar else None
        nereden = nereden or "İstanbul"
        nereye = detaylar.get("nereye") if detaylar else None
        tarih = detaylar.get("tarih") if detaylar else None
        yolcu = detaylar.get("kişi", 1) if detaylar else 1

        if not nereye:
            diyalog_durumu = {"aktif": True, "adım": "uçak_nereye", "veri": {"nereden": nereden, "yolcu": yolcu}}
            return "Nereye uçmak istiyorsunuz?"

        if not tarih:
            diyalog_durumu = {"aktif": True, "adım": "uçak_tarih", "veri": {"nereden": nereden, "nereye": nereye, "yolcu": yolcu}}
            return f"{nereden} → {nereye} için hangi tarihte uçmak istiyorsunuz?"

        sonuç = uçakları_karşılaştır(nereden, nereye, tarih, yolcu)
        if isinstance(sonuç, tuple):
            cevap, uçuşlar = sonuç
            diyalog_durumu = {
                "aktif": True, "adım": "uçak_seçim",
                "veri": {"nereden": nereden, "nereye": nereye, "tarih": tarih, "yolcu": yolcu, "uçuşlar": uçuşlar}
            }
            return cevap
        return sonuç

    return "Otel mi, uçak mı, yoksa restoran mı arayayım?"


def diyalog_devam(metin: str) -> str:
    global diyalog_durumu
    adım = diyalog_durumu.get("adım")
    veri = diyalog_durumu.get("veri", {})
    metin_lower = metin.lower().strip()

    if adım == "otel_şehir":
        şehir = metin.strip().title()
        if len(şehir) < 2:
            return "Şehir adını tekrar söyler misiniz?"
        diyalog_durumu = {"aktif": True, "adım": "otel_şehir_onay", "veri": {"şehir": şehir}}
        return f"{şehir} için otel arayayım, doğru mu?"

    elif adım == "otel_şehir_onay":
        if any(k in metin_lower for k in ["evet", "doğru", "tamam", "olur"]):
            şehir = veri["şehir"]
            giriş = veri.get("giriş")
            çıkış = veri.get("çıkış")
            kişi = veri.get("kişi", 2)
            if giriş and çıkış:
                sonuç = otelleri_karşılaştır(şehir, giriş, çıkış, kişi)
                if isinstance(sonuç, tuple):
                    cevap, oteller = sonuç
                    diyalog_durumu = {
                        "aktif": True, "adım": "otel_seçim",
                        "veri": {"şehir": şehir, "giriş": giriş, "çıkış": çıkış, "kişi": kişi, "oteller": oteller}
                    }
                    return cevap
                diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
                return sonuç
            elif giriş:
                diyalog_durumu = {"aktif": True, "adım": "otel_çıkış", "veri": {"şehir": şehir, "giriş": giriş, "kişi": kişi}}
                return "Çıkış tarihi ne olsun?"
            else:
                diyalog_durumu = {"aktif": True, "adım": "otel_giriş", "veri": {"şehir": şehir, "kişi": kişi}}
                return "Giriş tarihi ne olsun?"
        else:
            diyalog_durumu = {"aktif": True, "adım": "otel_şehir", "veri": {}}
            return "Hangi şehirde otel arayayım?"

    elif adım == "otel_giriş":
        tarih = tarih_parse(metin)
        if tarih:
            diyalog_durumu["adım"] = "otel_çıkış"
            diyalog_durumu["veri"]["giriş"] = tarih
            return "Çıkış tarihi ne olsun?"
        return "Anlamadım, örnek: 5 Haziran veya 2026-06-05"

    elif adım == "otel_çıkış":
        tarih = tarih_parse(metin)
        if tarih:
            diyalog_durumu["veri"]["çıkış"] = tarih
            diyalog_durumu["adım"] = "otel_kişi"
            return "Kaç kişilik oda olsun?"
        return "Anlamadım, örnek: 8 Haziran"

    elif adım == "otel_kişi":
        kişi = sözel_sayı_parse(metin)
        veri = diyalog_durumu["veri"]
        sonuç = otelleri_karşılaştır(veri["şehir"], veri["giriş"], veri["çıkış"], kişi)
        if isinstance(sonuç, tuple):
            cevap, oteller = sonuç
            diyalog_durumu = {
                "aktif": True, "adım": "otel_seçim",
                "veri": {**veri, "kişi": kişi, "oteller": oteller}
            }
            return cevap
        diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
        return sonuç

    elif adım == "otel_seçim":
        seçim_no = sözel_sayı_parse(metin) - 1
        oteller = veri.get("oteller", [])

        if 0 <= seçim_no < len(oteller):
            otel = oteller[seçim_no]
            if otel.get("link"):
                import webbrowser
                webbrowser.open(otel["link"])
            from database import rezervasyon_kaydet
            rezervasyon_kaydet(
                tür="otel",
                şehir=veri["şehir"],
                giriş=datetime.strptime(veri["giriş"], "%Y-%m-%d"),
                çıkış=datetime.strptime(veri["çıkış"], "%Y-%m-%d"),
                kişi=veri.get("kişi", 2),
                detaylar=otel
            )
            diyalog_durumu["adım"] = "uçak_öneri"
            diyalog_durumu["veri"]["seçilen_otel"] = otel
            return (
                f"{otel['ad']} seçildi ve rezervasyon sayfası açıldı. "
                f"{veri['şehir']} için uçak bileti de ayarlamamı ister misiniz?"
            )

        if any(k in metin_lower for k in ["hayır", "yok", "gerek yok", "istemiyorum"]):
            diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
            return "Tamam, rezervasyon işlemi tamamlandı."

        return f"Hangi oteli seçmek istiyorsunuz? 1 ile {len(oteller)} arasında numara söyleyin."

    elif adım == "uçak_öneri":
        if any(k in metin_lower for k in ["evet", "olur", "istiyorum", "ayarla", "tabii", "tamam"]):
            şehir = veri.get("şehir", "")
            giriş = veri.get("giriş", "")
            kişi = veri.get("kişi", 1)
            sonuç = uçakları_karşılaştır("İstanbul", şehir, giriş, kişi)
            if isinstance(sonuç, tuple):
                cevap, uçuşlar = sonuç
                diyalog_durumu = {
                    "aktif": True, "adım": "uçak_seçim",
                    "veri": {**veri, "nereden": "İstanbul", "nereye": şehir, "tarih": giriş, "uçuşlar": uçuşlar}
                }
                return cevap
            diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
            return sonuç
        diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
        return "Tamam, iyi tatiller!"

    elif adım == "uçak_nereye":
        nereye = metin.strip().title()
        diyalog_durumu["veri"]["nereye"] = nereye
        diyalog_durumu["adım"] = "uçak_tarih"
        return f"{veri.get('nereden', 'İstanbul')} → {nereye} için hangi tarihte uçmak istiyorsunuz?"

    elif adım == "uçak_tarih":
        tarih = tarih_parse(metin)
        if tarih:
            veri["tarih"] = tarih
            yolcu = veri.get("yolcu", 1)
            sonuç = uçakları_karşılaştır(veri.get("nereden", "İstanbul"), veri["nereye"], tarih, yolcu)
            if isinstance(sonuç, tuple):
                cevap, uçuşlar = sonuç
                diyalog_durumu = {
                    "aktif": True, "adım": "uçak_seçim",
                    "veri": {**veri, "uçuşlar": uçuşlar}
                }
                return cevap
            diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
            return sonuç
        return "Anlamadım, örnek: 5 Haziran veya 2026-06-05"

    elif adım == "uçak_seçim":
        sayı = re.search(r'\d+', metin)
        if sayı:
            seçim = int(sayı.group()) - 1
            uçuşlar = veri.get("uçuşlar", [])
            if 0 <= seçim < len(uçuşlar):
                uçuş = uçuşlar[seçim]
                from database import rezervasyon_kaydet
                rezervasyon_kaydet(
                    tür="uçak",
                    nereden=veri.get("nereden", "İstanbul"),
                    nereye=veri.get("nereye"),
                    giriş=datetime.strptime(veri["tarih"], "%Y-%m-%d"),
                    kişi=veri.get("yolcu", 1),
                    detaylar=uçuş
                )
                diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
                return f"{uçuş['havayolu']} seçildi. Rezervasyonunuz kaydedildi!"

        if any(k in metin_lower for k in ["hayır", "yok", "istemiyorum"]):
            diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
            return "Tamam."

        return "Hangi uçuşu seçmek istiyorsunuz? Numara söyleyin."

    diyalog_durumu = {"aktif": False, "adım": None, "veri": {}}
    return "Anlayamadım, tekrar söyler misiniz?"


def rezervasyon_işle(metin: str, detaylar: dict) -> str:
    from database import rezervasyonları_getir
    geçmiş = rezervasyonları_getir()
    if diyalog_durumu.get("aktif"):
        return diyalog_devam(metin)
    return rezervasyon_diyalogu(metin, detaylar, geçmiş)