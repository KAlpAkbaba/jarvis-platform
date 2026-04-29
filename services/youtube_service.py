# -*- coding: utf-8 -*-
import requests
from datetime import datetime

YOUTUBE_API_KEY = "***REMOVED***"
YOUTUBE_BASE = "https://www.googleapis.com/youtube/v3"

class YouTubeService:
    def search_videos(self, query: str, max_results: int = 5) -> str:
        """YouTube'da video ara, en yenileri getir."""
        try:
            from datetime import datetime, timedelta
            three_months_ago = (datetime.utcnow() - timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%SZ')
            r = requests.get(f"{YOUTUBE_BASE}/search", params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "order": "date",
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
                "relevanceLanguage": "tr",
                "publishedAfter": three_months_ago,
            })
            items = r.json().get("items", [])
            if not items:
                return "YouTube'da sonuç bulunamadı."
            lines = [f"📺 YouTube'da \"{query}\" için en yeni videolar:\n"]
            for item in items:
                snip = item["snippet"]
                vid_id = item["id"]["videoId"]
                title = snip.get("title", "")
                channel = snip.get("channelTitle", "")
                published = snip.get("publishedAt", "")[:10]
                url = f"https://youtube.com/watch?v={vid_id}"
                lines.append(f"• **{title}**\n  {channel} · {published}\n  {url}\n")
            return "\n".join(lines)
        except Exception as e:
            return f"YouTube arama hatası: {e}"

    def get_channel_videos(self, channel_name: str, max_results: int = 5) -> str:
        """Kanal adına göre en yeni videoları getir."""
        try:
            # Kanalı tam adıyla ara
            r = requests.get(f"{YOUTUBE_BASE}/search", params={
                "part": "snippet",
                "q": channel_name + " official channel",
                "type": "channel",
                "maxResults": 3,
                "key": YOUTUBE_API_KEY,
            })
            items = r.json().get("items", [])
            if not items:
                return f"\"{channel_name}\" adında kanal bulunamadı."
            # En iyi eşleşen kanalı seç (isim benzerliği)
            channel_id = items[0]["id"]["channelId"]
            channel_title = items[0]["snippet"]["title"]
            for item in items:
                if channel_name.lower() in item["snippet"]["title"].lower():
                    channel_id = item["id"]["channelId"]
                    channel_title = item["snippet"]["title"]
                    break
            # Kanalın son videolarını getir
            from datetime import datetime, timedelta
            one_year_ago = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
            r2 = requests.get(f"{YOUTUBE_BASE}/search", params={
                "part": "snippet",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
                "publishedAfter": one_year_ago,
            })
            videos = r2.json().get("items", [])
            if not videos:
                return f"{channel_title} kanalında video bulunamadı."
            lines = [f"📺 **{channel_title}** kanalının en yeni videoları:\n"]
            for v in videos:
                snip = v["snippet"]
                vid_id = v["id"]["videoId"]
                title = snip.get("title", "")
                published = snip.get("publishedAt", "")[:10]
                url = f"https://youtube.com/watch?v={vid_id}"
                lines.append(f"• **{title}**\n  {published} · {url}\n")
            return "\n".join(lines)
        except Exception as e:
            return f"Kanal video hatası: {e}"

    def get_video_stats(self, video_url: str) -> str:
        """Video URL'sinden istatistikleri getir."""
        try:
            import re
            match = re.search(r"v=([a-zA-Z0-9_-]{11})", video_url)
            if not match:
                return "Geçersiz YouTube URL'si."
            vid_id = match.group(1)
            r = requests.get(f"{YOUTUBE_BASE}/videos", params={
                "part": "snippet,statistics",
                "id": vid_id,
                "key": YOUTUBE_API_KEY,
            })
            items = r.json().get("items", [])
            if not items:
                return "Video bulunamadı."
            item = items[0]
            snip = item["snippet"]
            stats = item.get("statistics", {})
            title = snip.get("title", "")
            channel = snip.get("channelTitle", "")
            published = snip.get("publishedAt", "")[:10]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            desc = snip.get("description", "")[:200]
            return f"""📺 **{title}**
Kanal: {channel}
Tarih: {published}
Görüntülenme: {views:,} · Beğeni: {likes:,} · Yorum: {comments:,}
Açıklama: {desc}...
URL: https://youtube.com/watch?v={vid_id}"""
        except Exception as e:
            return f"Video istatistik hatası: {e}"
