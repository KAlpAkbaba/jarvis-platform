# -*- coding: utf-8 -*-
import threading
import time
from datetime import datetime
from typing import Callable
from core.config import config


class WeatherService:
    def __init__(self, search_fn: Callable, speak_fn: Callable, llm_fn: Callable):
        self.search = search_fn
        self.speak = speak_fn
        self.summarize = llm_fn
        self.settings = {"active": config.weather_enabled, "time": config.weather_time, "city": config.weather_city}
        self._notified = set()

    def configure(self, city=None, time=None, active=None):
        if city: self.settings["city"] = city
        if time: self.settings["time"] = time
        if active is not None: self.settings["active"] = active

    def start(self):
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        print("Hava bildirimi sistemi baslatildi!")

    def _loop(self):
        while True:
            try:
                if self.settings["active"]:
                    now = datetime.now()
                    if now.strftime("%H:%M") == self.settings["time"]:
                        today = now.strftime("%Y-%m-%d")
                        if today not in self._notified:
                            city = self.settings["city"]
                            raw = self.search(city)
                            summary = self.summarize(f"{city} hava durumu", raw)
                            msg = f"Gunaydin! {city} hava durumu: {summary}"
                            print(f"\n {msg}")
                            self.speak(msg)
                            self._notified.add(today)
                    if len(self._notified) > 7:
                        self._notified.clear()
            except Exception as e:
                print(f"Hava bildirimi hatasi: {e}")
            time.sleep(30)
