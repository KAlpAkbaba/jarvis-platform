# -*- coding: utf-8 -*-
import re
from typing import Optional

KEYWORD_RULES = {
    "ses_artir": ["sesi artir", "sesi ac", "ses ac", "ses artir"],
    "ses_azalt": ["sesi azalt", "sesi kis", "ses kis", "ses azalt"],
    "ses_kapat": ["sesi kapat", "sustur", "ses kapat"],
    "medya_durdur": ["durdur", "devam et", "pause"],
    "netflix": ["netflix"],
    "muzik": ["cal", "muzik cal", "sarki cal", "youtube"],
    "notlar": ["notlarim", "notlari goster", "notlarimi", "notlar", "notlari oku"],
    "gecmis_notlar": ["gecmis notlar", "eski notlar", "arsiv"],
    "hatirlaticilar": ["hatirlaticilarim", "hatirlatmalar", "planlarim", "planlarimi goster"],
    "rezervasyonlar": ["rezervasyonlarim", "rezervasyonlari goster"],
    "not_sil": ["notu sil", "notu tamamla", "notu kaldir", "sil notu"],
    "hava_bildirimi_ac": ["sabah bildirimi", "hava bildirimi", "hava durumu bildirimi"],
    "hava_bildirimi_kapat": ["hava bildirimini kapat", "bildirimi kapat"],
}

TR_MAP = {
    '\u0131': 'i', '\u0130': 'i', '\u011f': 'g', '\u011e': 'g',
    '\u00fc': 'u', '\u00dc': 'u', '\u015f': 's', '\u015e': 's',
    '\u00f6': 'o', '\u00d6': 'o', '\u00e7': 'c', '\u00c7': 'c',
}

def normalize(text):
    for k, v in TR_MAP.items():
        text = text.replace(k, v)
    return text.lower()


class Router:
    def route(self, text: str) -> Optional[str]:
        text_norm = normalize(text.lower().strip())
        for intent, keywords in KEYWORD_RULES.items():
            if any(k in text_norm for k in keywords):
                return intent
        return None

    def extract_number(self, text: str) -> Optional[int]:
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None

    def extract_verbal_number(self, text: str) -> int:
        verbal = {
            "bir": 1, "iki": 2, "uc": 3, "dort": 4, "bes": 5,
            "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10,
            "pir": 1,
        }
        text_norm = normalize(text.lower())
        num = self.extract_number(text)
        if num:
            return num
        for word, val in verbal.items():
            if word in text_norm:
                return val
        return 1