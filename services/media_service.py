# -*- coding: utf-8 -*-
import webbrowser
from urllib.parse import quote
import pyautogui


class MediaService:
    def youtube_search(self, query):
        if not query:
            return "Aranacak icerik belirtilmedi."
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote(query)}")
        return f"{query} YouTube'da aranıyor."

    def youtube_music(self, query):
        if not query:
            return "Aranacak muzik belirtilmedi."
        webbrowser.open(f"https://music.youtube.com/search?q={quote(query)}")
        return f"{query} YouTube Music'te aranıyor."

    def netflix_open(self, query=""):
        url = f"https://www.netflix.com/search?q={quote(query)}" if query else "https://www.netflix.com"
        webbrowser.open(url)
        return f"Netflix aciliyor."

    def volume_up(self):
        for _ in range(3): pyautogui.press("volumeup")
        return "Ses artirildi."

    def volume_down(self):
        for _ in range(3): pyautogui.press("volumedown")
        return "Ses azaltildi."

    def volume_mute(self):
        pyautogui.press("volumemute")
        return "Ses kapatildi."

    def media_play_pause(self):
        pyautogui.press("playpause")
        return "Oynatma/duraklatma."

    def handle(self, text, query=""):
        text_lower = text.lower()
        if "netflix" in text_lower:
            return self.netflix_open(query)
        elif any(k in text_lower for k in ["muzik", "sarki"]):
            return self.youtube_music(query)
        return self.youtube_search(query)
