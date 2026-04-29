# -*- coding: utf-8 -*-
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict
from clients.ollama_client import OllamaClient
from core.config import config


class LLMService:
    def __init__(self):
        self.client = OllamaClient(model=config.llm_model)

    def _system_prompt(self, mode: str = "hizli"):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        saat = now.strftime("%H:%M")
        yarin = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        oburgunu = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        mode_hint = "Kisa ve oz yanit ver." if mode == "hizli" else "Kapsamli ve detayli yanit ver, alt basliklar kullan."
        return f"""Senin adin Jarvis. Aktivra sirketi tarafindan gelistirildin. Kullanicilara kendini tanitmak icin "Ben Jarvis, Aktivra tarafindan gelistirilmis bir yapay zeka asistaniyim." diyebilirsin. KESINLIKLE sadece Turkce yaz, asla yabanci karakter kullanma. MOD: {mode_hint}
Bugun: {today}, Saat: {saat}, Yarin: {yarin}, Oburgunu: {oburgunu}

Asagidaki JSON formatinda yanit ver. Baska hicbir sey yazma:
{{"kategori":"SOHBET","yanit":"kisa Turkce cevap","not_icerik":null,"hatirlatma_zamani":null,"medya_sorgu":null,"rezervasyon_detay":{{"tur":null,"sehir":null,"nereden":null,"nereye":null,"tarih":null,"giris_tarihi":null,"cikis_tarihi":null,"kisi":1}}}}

KATEGORI KURALLARI (dikkatli sec):
- NOT_AL: "not al", "kaydet", "yaz" ile baslayan mesajlar
- HATIRLATICI: "hatirlatma", "alarm", "beni uyard" iceren mesajlar
- WEB_ARAMA: "kim", "ne", "nedir", "nasil", "neden", "hava", "haber", "kac", "kacinci", "hangi", "nerede", "tarih", "bilgi ver", "anlat", "acikla" iceren TUM bilgi sorulari
- MEDYA: "cal", "ac", "oynat", "muzik", "netflix", "youtube"
- REZERVASYON: "otel", "ucak", "bilet", "rezervasyon"
- SOHBET: SADECE selamlasma ("merhaba", "nasilsin", "naber", "iyi gunler") ve kisa sohbet

ONEMLI: Bilgi sorulari (kim, ne, nedir, nasil, neden, anlat, acikla) MUTLAKA WEB_ARAMA olmali!

NOT_AL icin not_icerik alani sadece kaydedilecek icerigi icermeli. Ornek:
Kullanici: "not al yarin toplantim var" -> not_icerik: "yarin toplantim var"

Sadece JSON dondur, baska hicbir aciklama yapma."""

    def process(self, text, history=None, mode: str = "hizli"):
        history = history or []
        messages = [{"role": "system", "content": self._system_prompt(mode)}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": text})
        try:
            raw = self.client.chat(messages,
                num_predict=config.llm_num_predict,
                temperature=config.llm_temperature,
                top_k=config.llm_top_k,
                top_p=config.llm_top_p,
                repeat_penalty=config.llm_repeat_penalty,
                num_ctx=config.llm_num_ctx)
            
            # JSON temizle
            raw = raw.strip()
            raw = re.sub(r"`json|`", "", raw).strip()
            
            # JSON bul
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                raw = match.group()
            
            data = json.loads(raw)
            return {
                "kategori": data.get("kategori", "SOHBET"),
                "yanit": data.get("yanit") or "Anliyorum.",
                "not_icerik": data.get("not_icerik"),
                "hatirlatma_zamani": data.get("hatirlatma_zamani"),
                "medya_sorgu": data.get("medya_sorgu"),
                "rezervasyon_detay": data.get("rezervasyon_detay"),
            }
        except json.JSONDecodeError:
            # JSON parse basarisiz — sohbet olarak isle
            try:
                sohbet = self.client.chat([
                    {"role": "system", "content": "Sen yardimci bir Turkce asistansin. Kisa ve oz yanit ver."},
                    {"role": "user", "content": text}
                ], num_predict=200)
                return {"kategori": "SOHBET", "yanit": sohbet,
                        "not_icerik": None, "hatirlatma_zamani": None,
                        "medya_sorgu": None, "rezervasyon_detay": None}
            except:
                return {"kategori": "SOHBET", "yanit": "Evet, sizi dinliyorum.",
                        "not_icerik": None, "hatirlatma_zamani": None,
                        "medya_sorgu": None, "rezervasyon_detay": None}
        except Exception as e:
            return {"kategori": "SOHBET", "yanit": "Bir sorun olustu, tekrar deneyin.",
                    "not_icerik": None, "hatirlatma_zamani": None,
                    "medya_sorgu": None, "rezervasyon_detay": None}

    def summarize(self, question, search_result):
        if search_result and len(search_result) > 20:
            sistem = """Sen yalnizca TURKCE konusan bir yapay zeka asistansin.
Verilen bilgileri kullanarak soruyu detayli, akici ve zengin bir sekilde anlat.
Mitoloji veya tarih sorularinda hikayeleri canli anlat.
KESINLIKLE Turkce kullan, baska dil kullanma."""
            prompt = f"""Soru: {question}

Kaynak bilgiler:
{search_result[:1500]}

Bu bilgileri kullanarak soruyu detayli TURKCE olarak anlat. 
Hikaye veya mitoloji ise canli ve zengin anlat, kisaltma."""
        else:
            sistem = """Sen yalnizca TURKCE konusan bilgili bir yapay zeka asistansin.
Sorulari detayli, akici ve dogru sekilde cevapla.
Mitoloji veya tarih sorularinda hikayeleri canli anlat.
KESINLIKLE Turkce kullan."""
            prompt = f"""Soru: {question}

Bu soruyu kendi bilginle detayli TURKCE olarak cevapla.
Hikaye veya mitoloji ise canli ve zengin anlat, kisaltma."""
        try:
            return self.client.chat(
                [{"role": "system", "content": sistem},
                 {"role": "user", "content": prompt}],
                num_predict=2000,
                temperature=0.4,
                num_ctx=8192
            )
        except:
            return "Bilgi bulunamadi."

