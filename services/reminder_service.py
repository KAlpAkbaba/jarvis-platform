# -*- coding: utf-8 -*-
import threading
import time
from datetime import datetime
from typing import Callable, Set
from database.repository import get_pending_reminders, archive_expired_reminders


class ReminderService:
    def __init__(self, speak_fn: Callable):
        self.speak = speak_fn
        self._notified: Set[int] = set()
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        print("Hatirlatici sistemi baslatildi!")

    def _loop(self):
        while self._running:
            try:
                for note_id, content, remind_at in get_pending_reminders():
                    if note_id not in self._notified:
                        remaining = int((remind_at - datetime.now()).total_seconds() / 60)
                        msg = f"Hatirlatma: {remaining} dakika sonra {content}" if remaining > 0 else f"Hatirlatma: Su an {content}"
                        print(f"\n {msg}")
                        self.speak(msg)
                        self._notified.add(note_id)
                archive_expired_reminders()
                if len(self._notified) > 100:
                    self._notified.clear()
            except Exception as e:
                print(f"Hatirlatici hatasi: {e}")
            time.sleep(60)
