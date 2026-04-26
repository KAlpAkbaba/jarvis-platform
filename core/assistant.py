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

    def process(self, text: str) -> str:
        text_lower = text.lower().strip()

        # Takvim kontrolu
        takvim_goster = ["takvim", "etkinlik", "randevu", "ajanda"]
        takvim_ekle_kw = ["takvime ekle", "etkinlik ekle", "randevu ekle"]
        if any(k in text_lower for k in takvim_ekle_kw):
            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from datetime import datetime, timedelta
                creds = Credentials.from_authorized_user_file("/app/data/google_token.json", scopes=["https://www.googleapis.com/auth/calendar"])
                service = build("calendar", "v3", credentials=creds)
                dt_start = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
                dt_end = dt_start.replace(hour=11)
                event = {"summary": text, "start": {"dateTime": dt_start.isoformat(), "timeZone": "Europe/Istanbul"}, "end": {"dateTime": dt_end.isoformat(), "timeZone": "Europe/Istanbul"}}
                service.events().insert(calendarId="primary", body=event).execute()
                return "Etkinlik takvime eklendi!"
            except Exception as cal_err:
                return "Takvim hatasi: " + str(cal_err)
        elif any(k in text_lower for k in takvim_goster):
            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from datetime import datetime, timedelta
                creds = Credentials.from_authorized_user_file("/app/data/google_token.json", scopes=["https://www.googleapis.com/auth/calendar"])
                service = build("calendar", "v3", credentials=creds)
                now = datetime.utcnow().isoformat() + "Z"
                end_dt = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
                events = service.events().list(calendarId="primary", timeMin=now, timeMax=end_dt, maxResults=10, singleEvents=True, orderBy="startTime").execute().get("items", [])
                if not events:
                    google_result = "Google takviminde yaklasan etkinlik yok."
                else:
                    lines = ["Google takvimi:"]
                    for ev in events:
                        ev_title = ev.get("summary", "Basliksiz")
                        ev_start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
                        try:
                            ev_dt = datetime.fromisoformat(ev_start.replace("Z", "+00:00"))
                            ev_start = ev_dt.strftime("%d %B %Y %H:%M")
                        except Exception:
                            pass
                        lines.append("- " + ev_start + " : " + ev_title)
                    google_result = chr(10).join(lines)
            except Exception as cal_err2:
                google_result = "Google takvim hatasi: " + str(cal_err2)

            # Outlook takvimi de goster
            outlook_result = ""
            try:
                import json as _json, os as _os
                import requests as _req
                from datetime import datetime as _dt2, timedelta as _td2
                if _os.path.exists("/app/data/outlook_token.json"):
                    with open("/app/data/outlook_token.json") as _f:
                        _tok = _json.load(_f).get("access_token", "")
                    if _tok:
                        _headers = {"Authorization": "Bearer " + _tok}
                        _now = _dt2.utcnow().isoformat() + "Z"
                        _end = (_dt2.utcnow() + _td2(days=7)).isoformat() + "Z"
                        _url = "https://graph.microsoft.com/v1.0/me/calendarview?startDateTime=" + _now + "&endDateTime=" + _end + "&$top=10&$orderby=start/dateTime"
                        _res = _req.get(_url, headers=_headers)
                        _events = _res.json().get("value", [])
                        if _events:
                            _lines = ["Outlook takvimi:"]
                            for _e in _events:
                                _title = _e.get("subject", "Basliksiz")
                                _start = _e.get("start", {}).get("dateTime", "")
                                try:
                                    _edt = _dt2.fromisoformat(_start)
                                    _start = _edt.strftime("%d %B %Y %H:%M")
                                except Exception:
                                    pass
                                _lines.append("- " + _start + " : " + _title)
                            outlook_result = chr(10).join(_lines)
            except Exception:
                pass

            final = google_result
            if outlook_result:
                final = final + chr(10) + chr(10) + outlook_result
            return final


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

        # Bilgi sorgusu kontrolu - direkt web aramaya yonlendir
        bilgi_kelimeleri = ["nedir", "kimdir", "nerede", "nasil", "neden", "anlat",
                            "acikla", "bilgi ver", "tarihce", "hakkinda", "konusu nedir",
                            "kim", "ne zaman", "kac", "hangi", "bul", "goster"]
        baglam_kelimeleri = ["daha detayli", "devam et", "anlat", "acikla", "devam",
                             "peki", "ya", "ne oldu", "sonra", "neden", "nasil"]
        from core.router import normalize
        text_norm = normalize(text_lower)

        # Baglamsal soru - onceki konuyla ilgili
        if any(k in text_norm for k in baglam_kelimeleri) and len(self.context.messages) > 0:
            gecmis = self.context.last_n(6)
            gecmis_metin = "\n".join([f"{m['role']}: {m['content']}" for m in gecmis])
            prompt = f"""Onceki konusma:
{gecmis_metin}

Kullanici simdi soruyor: {text}
Onceki konusmayi dikkate alarak TURKCE olarak 3-5 cumleyle detayli cevap ver."""
            return self.llm.summarize(text, prompt)

        if any(k in text_norm for k in bilgi_kelimeleri):
            raw = self.search.search(text)
            if raw and raw != "Bilgi bulunamadi.":
                return self.llm.summarize(text, raw)

        # Matematik kontrolu
        import re as _re
        mat_keywords = ['carpi','carpı','bolu','bolü','arti','artı','eksi','hesapla','yuzde','yüzde','kac eder','kactir','kaçtır']
        mat_symbols = _re.search(r'\d+\s*[\+\-\*\/\^\%xX×÷]\s*\d+', text)
        has_number = bool(_re.search(r'\d', text_lower))
        has_math_word = any(k in text_lower for k in mat_keywords)
        # Not/hatirlatici icin matematik kontrolunu atla
        is_note = any(k in text_lower for k in ['not al','hatirlatici','kaydet','yaz '])
        if not is_note and ((has_number and has_math_word) or mat_symbols):
            mat_prompt = f'Bu matematik sorusunu hesapla ve SADECE sonucu yaz, aciklama yapma: {text}'
            try:
                from clients.ollama_client import OllamaClient
                client = OllamaClient()
                result_mat = client.chat(
                    [{"role":"system","content":"Sadece matematik hesapla, yalnizca sayisal sonucu yaz. Hic aciklama yapma."},{"role":"user","content":mat_prompt}],
                    num_predict=20, temperature=0.1
                )
                return result_mat
            except:
                return self.llm.summarize(text, "")

        # LLM ile isle
        result = self.llm.process(text, self.context.to_list())
        if result.get("not_icerik") and result.get("kategori") not in ["NOT_AL","HATIRLATICI"]:
            result["kategori"] = "NOT_AL"
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
            icerik = result.get("not_icerik")
            if not icerik:
                import re as _re
                icerik = _re.sub(r"^(not al|kaydet|yaz)[.:! ]*", "", text, flags=_re.IGNORECASE).strip()
            if not icerik:
                icerik = text
            return self.notes.add(icerik, category="genel")

        elif category == "HATIRLATICI":
            import re as _re6
            content = result.get("not_icerik")
            if not content:
                content = __import__("re").sub(r"^(hatirlatici ekle|hatirlatici|alarm)\s*", "", text, flags=__import__("re").IGNORECASE).strip()
            if not content:
                content = text
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


