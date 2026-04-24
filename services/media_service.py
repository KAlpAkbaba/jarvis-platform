import webbrowser
from urllib.parse import quote

class MediaService:
    def youtube_search(self, query):
        webbrowser.open("https://www.youtube.com/results?search_query=" + quote(query))
        return query + " YouTube da aranıyor."
    def youtube_music(self, query):
        webbrowser.open("https://music.youtube.com/search?q=" + quote(query))
        return query + " YouTube Music te aranıyor."
    def netflix_open(self, query=''):
        webbrowser.open("https://www.netflix.com" + ("/search?q=" + quote(query) if query else ""))
        return "Netflix aciliyor."
    def volume_up(self): return "Ses arttirildi."
    def volume_down(self): return "Ses azaltildi."
    def volume_mute(self): return "Ses kapatildi."
    def media_play_pause(self): return "Oynatma/duraklatma."
    def handle(self, text, query=''):
        if "netflix" in text.lower(): return self.netflix_open(query)
        return self.youtube_search(query)
