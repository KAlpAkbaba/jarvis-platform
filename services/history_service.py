import uuid
from datetime import datetime
from sqlalchemy import text
from database.db import SessionLocal

class HistoryService:
    def create_session(self) -> str:
        return str(uuid.uuid4())[:8]

    def save_message(self, session_id: str, role: str, content: str, user_id: int = None):
        try:
            db = SessionLocal()
            db.execute(text(
                "INSERT INTO sohbet_gecmisi (session_id, role, content, kullanici_id) VALUES (:s, :r, :c, :u)"
            ), {"s": session_id, "r": role, "c": content, "u": user_id})
            db.commit()
            db.close()
        except Exception as e:
            print(f"History kayit hatasi: {e}")

    def get_session(self, session_id: str, limit: int = 20):
        try:
            db = SessionLocal()
            result = db.execute(text(
                "SELECT role, content, created_at FROM sohbet_gecmisi WHERE session_id = :s ORDER BY created_at ASC LIMIT :l"
            ), {"s": session_id, "l": limit}).fetchall()
            db.close()
            return [{"role": r[0], "content": r[1], "time": str(r[2])} for r in result]
        except Exception as e:
            print(f"History getir hatasi: {e}")
            return []

    def get_all_sessions(self, user_id: int = None):
        try:
            db = SessionLocal()
            if user_id:
                result = db.execute(text("""
                    SELECT session_id, MIN(created_at) as started, COUNT(*) as msg_count,
                           LEFT(MAX(CASE WHEN role='user' THEN content END), 50) as preview
                    FROM sohbet_gecmisi
                    WHERE kullanici_id = :uid
                    GROUP BY session_id
                    ORDER BY started DESC
                    LIMIT 20
                """), {"uid": user_id}).fetchall()
            else:
                result = db.execute(text("""
                    SELECT session_id, MIN(created_at) as started, COUNT(*) as msg_count,
                           LEFT(MAX(CASE WHEN role='user' THEN content END), 50) as preview
                    FROM sohbet_gecmisi
                    GROUP BY session_id
                    ORDER BY started DESC
                    LIMIT 20
                """)).fetchall()
            db.close()
            return [{"session_id": r[0], "started": str(r[1]), "msg_count": r[2], "preview": r[3]} for r in result]
        except Exception as e:
            print(f"Sessions getir hatasi: {e}")
            return []

    def delete_session(self, session_id: str):
        try:
            db = SessionLocal()
            db.execute(text("DELETE FROM sohbet_gecmisi WHERE session_id = :s"), {"s": session_id})
            db.commit()
            db.close()
            return True
        except Exception as e:
            print(f"Session sil hatasi: {e}")
            return False

    def search_history(self, query: str, limit: int = 5):
        try:
            db = SessionLocal()
            result = db.execute(text("""
                SELECT session_id, role, content, created_at
                FROM sohbet_gecmisi
                WHERE content ILIKE :q
                ORDER BY created_at DESC
                LIMIT :l
            """), {"q": f"%{query}%", "l": limit}).fetchall()
            db.close()
            return [{"session_id": r[0], "role": r[1], "content": r[2], "time": str(r[3])} for r in result]
        except Exception as e:
            print(f"History ara hatasi: {e}")
            return []
