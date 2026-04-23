import webbrowser
import subprocess
import urllib.parse
import time
import pyautogui
import yt_dlp

def youtube_ilk_url(sorgu: str) -> str:
    """Arama sonucundaki ilk videonun URL'sini döndür"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch1',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sonuç = ydl.extract_info(f"ytsearch1:{sorgu}", download=False)
            if sonuç and 'entries' in sonuç and sonuç['entries']:
                video_id = sonuç['entries'][0]['id']
                return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        print(f"yt-dlp hatası: {e}")
    return None

def youtube_aç(sorgu: str) -> str:
    url = youtube_ilk_url(sorgu)
    if url:
        webbrowser.open(url)
        return f"YouTube'da '{sorgu}' oynatılıyor."
    else:
        # Fallback — arama sayfasını aç
        encoded = urllib.parse.quote(sorgu)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        return f"YouTube'da '{sorgu}' aranıyor."

def youtube_müzik_aç(sorgu: str) -> str:
    # Müzik için YouTube Music yerine YouTube'da lyrics/official video ara
    url = youtube_ilk_url(f"{sorgu} official video")
    if url:
        webbrowser.open(url)
        return f"'{sorgu}' oynatılıyor."
    return youtube_aç(sorgu)

def netflix_aç(sorgu: str = "") -> str:
    try:
        if sorgu:
            encoded = urllib.parse.quote(sorgu)
            url = f"https://www.netflix.com/search?q={encoded}"
        else:
            url = "https://www.netflix.com"
        webbrowser.open(url)
        return f"Netflix'te '{sorgu}' açılıyor." if sorgu else "Netflix açılıyor."
    except Exception as e:
        return f"Netflix açılırken hata: {str(e)}"

def medyayı_durdur() -> str:
    try:
        pyautogui.press('space')
        return "Medya duraklatıldı."
    except Exception as e:
        return f"Hata: {str(e)}"

def ses_ayarla(yön: str) -> str:
    try:
        if yön in ["artır", "aç", "yükselt"]:
            for _ in range(5):
                pyautogui.press('volumeup')
            return "Ses artırıldı."
        elif yön in ["azalt", "kıs", "düşür"]:
            for _ in range(5):
                pyautogui.press('volumedown')
            return "Ses azaltıldı."
        elif yön in ["kapat", "sustur"]:
            pyautogui.press('volumemute')
            return "Ses kapatıldı."
    except Exception as e:
        return f"Hata: {str(e)}"

def medya_komutu_işle(metin: str, medya_sorgu: str = "") -> str:
    metin_lower = metin.lower()
    sorgu = medya_sorgu or metin

    if any(k in metin_lower for k in ["durdur", "beklet", "devam et"]):
        return medyayı_durdur()

    if any(k in metin_lower for k in ["sesi artır", "sesi aç", "sesi yükselt"]):
        return ses_ayarla("artır")
    if any(k in metin_lower for k in ["sesi azalt", "sesi kıs", "sesi düşür"]):
        return ses_ayarla("azalt")
    if any(k in metin_lower for k in ["sesi kapat", "sustur"]):
        return ses_ayarla("kapat")

    if any(k in metin_lower for k in ["netflix", "film", "dizi"]):
        temiz = sorgu.lower()
        for k in ["netflix", "film", "dizi", "aç", "oynat", "izle"]:
            temiz = temiz.replace(k, "").strip()
        return netflix_aç(temiz)

    if any(k in metin_lower for k in ["müzik", "şarkı", "çal", "dinle"]):
        temiz = sorgu.lower()
        for k in ["müzik", "şarkı", "çal", "dinle", "aç"]:
            temiz = temiz.replace(k, "").strip()
        return youtube_müzik_aç(temiz.strip())

    return youtube_aç(sorgu)

# Test
if __name__ == "__main__":
    print(youtube_aç("Tarkan Şımarık"))

