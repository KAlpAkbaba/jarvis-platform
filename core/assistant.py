import re
from datetime import datetime
from typing import Optional

from core.config import config
from core.context import ConversationContext
from core.router import Router
from core.session import Session
from services.llm_service import LLMService
from services.stt_service import STTService
from services.tts_service import TTSService
from services.search_service import SearchService
from services.note_service import NoteService
from services.media_service import MediaService
from services.weather_service import WeatherService
from skills.reservation import ReservationSkill
from database.repository import (
    save_conversation, get_reservations, time_expression
)


class Assistant:
    def __init__(self):
        self.llm = LLMService()
        self.stt = STTService()
        self.tts = TTSService()
        self.search = SearchService()
        self.notes = NoteService()
        self.media = MediaService()
        self.router = Router()
        self.context = ConversationContext()
        self.reservation = ReservationSkill()
        self.weather = WeatherService(
            search_fn=self.search.weather,
            speak_fn=self.tts.speak,
            llm_fn=self.llm.summarize,
        )

    def speak(self, text: str):
        print(f"Asistan: {text}")
        self.tts.speak(text)

    def process(self, text: str) -> str:
        text_lower = text.lower().strip()

        # Aktif rezervasyon diyalogu
        if self.reservation.dialog_active():
            return self.reservation.continue_dialog(text)

        # Kural tabanli y�nlendirme
        intent = self.router.route(text)

        if intent == "ses_artir":
            return self.media.volume_up()
        elif intent == "ses_azalt":
            return self.media.volume_down()
        elif intent == "ses_kapat":
            return self.media.volume_mute()
        elif intent == "medya_durdur":
            return self.media.media_play_pause()
        elif intent == "muzik":
            query = text_lower
            for k in ["�al", "m�zik", "sarki", "youtube", "a�", "oynat"]:
                query = query.replace(k, "").strip()
            return self.media.youtube_music(query) if query else self.media.youtube_search("m�zik")
        elif intent == "netflix":
            query = text_lower
            for k in ["netflix", "a�", "baslat"]:
                query = query.replace(k, "").strip()
            return self.media.netflix_open(query)
        elif intent == "notlar":
            return self.notes.list()
        elif intent == "gecmis_notlar":
            return self.notes.list_archived()
        elif intent == "hatirlaticilar":
            return self.notes.list_reminders()
        elif intent == "rezervasyonlar":
            rezervasyonlar = get_reservations()
            if not rezervasyonlar:
                return "Kayitli rezervasyonunuz yok."
            cevap = "Rezervasyonlariniz. "
            for i, r in enumerate(rezervasyonlar, 1):
                if r["type"] == "otel":
                    cevap += f"{i}. {r['city']} oteli, {r['check_in'].strftime('%d %B') if r['check_in'] else ''}. "
                elif r["type"] == "u�ak":
                    cevap += f"{i}. {r['from_city']} {r['to_city']} u�usu. "
            return cevap.strip()
        elif intent == "not_sil":
            sayi = self.router.extract_number(text)
            if sayi:
                ids = self.notes.get_all_ids()
                if sayi in ids:
                    return self.notes.delete(sayi)
            if any(k in text_lower for k in ["son", "sonuncu"]):
                return self.notes.delete_last()
            return self.notes.list() + " Numara s�yleyin."
        elif intent == "hava_bildirimi_ac":
            saat_match = re.search(r'(\d{1,2})[:\.]?(\d{2})?', text)
            if saat_match:
                saat = saat_match.group(1).zfill(2)
                dakika = saat_match.group(2) or "00"
                saat_str = f"{saat}:{dakika}"
                sehir = "stanbul"
                for s in ["istanbul", "ankara", "izmir", "bursa", "antalya"]:
                    if s in text_lower:
                        sehir = s.capitalize()
                        break
                self.weather.configure(city=sehir, time=saat_str, active=True)
                return f"Hava durumu bildirimi her sabah {saat_str}'de {sehir} i�in gelecek."
            self.weather.configure(active=True)
            return f"Hava durumu bildirimi aktif."
        elif intent == "hava_bildirimi_kapat":
            self.weather.configure(active=False)
            return "Hava durumu bildirimi kapatildi."

        # LLM ile isle
        result = self.llm.process(text, self.context.to_list())
        category = result["category"] if "category" in result else result.get("kategori", "SOHBET")
        answer = result.get("yanit", "Anliyorum.")

        if category == "WEB_ARAMA":
            if any(k in text_lower for k in ["hava", "sicaklik", "yagmur"]):
                sehir = "stanbul"
                for s in ["istanbul", "ankara", "izmir", "bursa", "antalya"]:
                    if s in text_lower:
                        sehir = s.capitalize()
                raw = self.search.weather(sehir)
            elif any(k in text_lower for k in ["haber", "g�ndem"]):
                raw = self.search.news(text)
            else:
                raw = self.search.search(text)
            return self.llm.summarize(text, raw)

        elif category == "MEDYA":
            query = result.get("medya_sorgu") or text
            return self.media.handle(text, query)

        elif category == "NOT_AL":
            content = result.get("not_i�erik") or text
            return self.notes.add(content, category="genel")

        elif category == "HATIRLATICI":
            content = result.get("not_i�erik") or text
            remind_str = result.get("hatirlatma_zamani")
            remind_at = None
            if remind_str:
                try:
                    remind_at = datetime.strptime(remind_str, "%Y-%m-%d %H:%M")
                except:
                    pass
            self.notes.add(content, category="hatirlatici", remind_at=remind_at)
            if remind_at:
                return f"Hatirlatici kaydedildi. {content}. {time_expression(remind_at)}."
            return f"Hatirlatici kaydedildi: {content}"

        elif category == "REZERVASYON":
            details = result.get("rezervasyon_detay") or {}
            return self.reservation.handle(text, details)

        return answer if answer else "Anlayamadim, tekrar s�yler misiniz?"

    def update_history(self, user_text: str, assistant_text: str):
        self.context.add("user", user_text)
        self.context.add("assistant", assistant_text)
        save_conversation("user", user_text)
        save_conversation("assistant", assistant_text)


