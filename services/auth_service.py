import hashlib
import secrets
import os
from datetime import datetime, timedelta
from sqlalchemy import text
from database.db import SessionLocal

class AuthService:
    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{hashed}"

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            salt, hash_val = hashed.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == hash_val
        except:
            return False

    def create_token(self) -> str:
        return secrets.token_urlsafe(32)

    def register(self, email: str, isim: str, password: str) -> dict:
        try:
            db = SessionLocal()
            existing = db.execute(text("SELECT id FROM kullanicilar WHERE email = :e"), {"e": email}).fetchone()
            if existing:
                db.close()
                return {"error": "Bu email zaten kayitli"}
            sifre_hash = self.hash_password(password)
            result = db.execute(text(
                "INSERT INTO kullanicilar (email, isim, sifre_hash) VALUES (:e, :i, :s) RETURNING id"
            ), {"e": email, "i": isim, "s": sifre_hash})
            user_id = result.fetchone()[0]
            db.commit()
            token = self._create_session(db, user_id)
            db.close()
            return {"token": token, "user_id": user_id, "isim": isim, "email": email}
        except Exception as e:
            return {"error": str(e)}

    def login(self, email: str, password: str) -> dict:
        try:
            db = SessionLocal()
            user = db.execute(text(
                "SELECT id, isim, sifre_hash, avatar_url FROM kullanicilar WHERE email = :e"
            ), {"e": email}).fetchone()
            if not user:
                db.close()
                return {"error": "Kullanici bulunamadi"}
            if not self.verify_password(password, user[2] or ""):
                db.close()
                return {"error": "Sifre yanlis"}
            db.execute(text("UPDATE kullanicilar SET last_login = NOW() WHERE id = :id"), {"id": user[0]})
            db.commit()
            token = self._create_session(db, user[0])
            db.close()
            return {"token": token, "user_id": user[0], "isim": user[1], "email": email, "avatar_url": user[3]}
        except Exception as e:
            return {"error": str(e)}

    def oauth_login(self, email: str, isim: str, provider_id: str, provider: str, avatar_url: str = None) -> dict:
        try:
            db = SessionLocal()
            col = "google_id" if provider == "google" else "microsoft_id"
            user = db.execute(text(f"SELECT id, isim FROM kullanicilar WHERE email = :e"), {"e": email}).fetchone()
            if not user:
                result = db.execute(text(
                    f"INSERT INTO kullanicilar (email, isim, {col}, avatar_url) VALUES (:e, :i, :p, :a) RETURNING id, isim"
                ), {"e": email, "i": isim, "p": provider_id, "a": avatar_url})
                user = result.fetchone()
            else:
                db.execute(text(f"UPDATE kullanicilar SET {col} = :p, last_login = NOW() WHERE id = :id"), {"p": provider_id, "id": user[0]})
            db.commit()
            token = self._create_session(db, user[0])
            db.close()
            return {"token": token, "user_id": user[0], "isim": user[1], "email": email, "avatar_url": avatar_url}
        except Exception as e:
            return {"error": str(e)}

    def verify_token(self, token: str) -> dict:
        try:
            db = SessionLocal()
            result = db.execute(text("""
                SELECT k.id, k.isim, k.email, k.avatar_url
                FROM kullanici_sessiyonlari s
                JOIN kullanicilar k ON s.kullanici_id = k.id
                WHERE s.token = :t AND s.expires_at > NOW()
            """), {"t": token}).fetchone()
            db.close()
            if not result:
                return {"error": "Gecersiz token"}
            return {"user_id": result[0], "isim": result[1], "email": result[2], "avatar_url": result[3]}
        except Exception as e:
            return {"error": str(e)}

    def logout(self, token: str):
        try:
            db = SessionLocal()
            db.execute(text("DELETE FROM kullanici_sessiyonlari WHERE token = :t"), {"t": token})
            db.commit()
            db.close()
        except:
            pass

    def _create_session(self, db, user_id: int) -> str:
        token = self.create_token()
        expires = datetime.now() + timedelta(days=30)
        db.execute(text(
            "INSERT INTO kullanici_sessiyonlari (kullanici_id, token, expires_at) VALUES (:u, :t, :e)"
        ), {"u": user_id, "t": token, "e": expires})
        db.commit()
        return token
