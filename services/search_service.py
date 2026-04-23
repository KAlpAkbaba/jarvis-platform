# -*- coding: utf-8 -*-
import requests
from database.repository import save_knowledge, search_knowledge
from core.config import config


class SearchService:
    def __init__(self):
        self.url = config.searxng_url

    def _search(self, query, category="general"):
        try:
            r = requests.get(self.url,
                params={"q": query, "format": "json", "language": "tr", "categories": category},
                timeout=10)
            results = r.json().get("results", [])[:3]
            return "\n".join([f"{x.get('title','')}: {x.get('content','')}" for x in results])
        except Exception as e:
            print(f"SearxNG hatasi: {e}")
            return ""

    def search(self, query):
        cache = search_knowledge(query)
        if cache:
            print(f"Cache: {query}")
            return cache["answer"]
        result = self._search(query)
        if result and len(result) > 20:
            save_knowledge(query, result, "searxng")
        return result or "Bilgi bulunamadi."

    def weather(self, city):
        return self._search(f"{city} hava durumu bugun sicaklik hissedilen")

    def news(self, query):
        return self._search(query, category="news")
