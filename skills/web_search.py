import requests
from database import bilgi_kaydet, bilgi_ara

SEARXNG_URL = "http://localhost:8080/search"

def searxng_ara(sorgu: str, kategori: str = "general") -> str:
    try:
        response = requests.get(
            SEARXNG_URL,
            params={
                "q": sorgu,
                "format": "json",
                "language": "tr",
                "categories": kategori,
            },
            timeout=10
        )
        data = response.json()
        sonuçlar = data.get("results", [])[:3]
        if not sonuçlar:
            return "Sonuç bulunamadı."
        return "\n".join([
            f"{s.get('title', '')}: {s.get('content', '')}"
            for s in sonuçlar
        ])
    except Exception as e:
        print(f"SearxNG hatası: {e}")
        return ""

def web_ara(sorgu: str) -> str:
    # Cache kontrol — hava ve haberler hariç
    if not any(k in sorgu.lower() for k in ["hava", "haber", "gündem", "son dakika"]):
        cache = bilgi_ara(sorgu)
        if cache:
            print(f"📦 Cache'den bulundu: {sorgu}")
            return cache["yanıt"]

    # Sorguyu zenginleştir
    zengin_sorgu = sorgu
    if "nedir" in sorgu.lower() or "ne" in sorgu.lower():
        zengin_sorgu = f"{sorgu} açıklama bilgi"
    elif "kim" in sorgu.lower():
        zengin_sorgu = f"{sorgu} biyografi"
    elif "nasıl" in sorgu.lower():
        zengin_sorgu = f"{sorgu} adımlar yöntem"
    elif "ne zaman" in sorgu.lower():
        zengin_sorgu = f"{sorgu} tarih"

    sonuç = searxng_ara(zengin_sorgu)
    if sonuç and len(sonuç) > 20:
        bilgi_kaydet(sorgu, sonuç, "searxng")
    return sonuç if sonuç else "Bilgi bulunamadı."

def hava_durumu_ara(şehir: str) -> str:
    # Taze veri — cache yok
    return searxng_ara(
        f"{şehir} hava durumu bugün sıcaklık hissedilen nem yağmur",
        kategori="general"
    )

def haber_ara(sorgu: str) -> str:
    # Son 24 saat haberleri
    from datetime import datetime
    tarih = datetime.now().strftime("%d %B %Y")
    return searxng_ara(
        f"{sorgu} {tarih} son dakika",
        kategori="news"
    )

