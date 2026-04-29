import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy import text
from database.db import SessionLocal
import resend

resend.api_key = "***REMOVED***"

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

    def send_welcome_email(self, email: str, isim: str):
        try:
            resend.Emails.send({
                "from": "Jarvis AI <noreply@aktivra.com>",
                "to": email,
                "subject": "Jarvis AI'ya Hoş Geldiniz!",
                "html": f"""
                <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#0a0a0a;color:#f0f0f0;border-radius:16px;overflow:hidden">
                  <div style="background:#111;padding:32px;text-align:center;border-bottom:1px solid #222">
                    <div style="width:48px;height:48px;background:#fff;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#0a0a0a;margin-bottom:12px">J</div>
                    <h1 style="margin:0;font-size:20px;font-weight:700;letter-spacing:.04em">JARVIS AI</h1>
                  </div>
                  <div style="padding:36px 32px">
                    <h2 style="margin:0 0 12px;font-size:18px;font-weight:600">Hoş Geldiniz{', ' + isim if isim else ''}! 🎉</h2>
                    <p style="margin:0 0 20px;color:#888;font-size:14px;line-height:1.7">
                      Jarvis AI ailesine katıldığınız için teşekkür ederiz.<br>
                      Artık yapay zeka asistanınıza her an, her yerden erişebilirsiniz.
                    </p>
                    <div style="background:#1a1a1a;border-radius:12px;padding:20px;margin-bottom:20px">
                      <p style="margin:0 0 10px;font-size:13px;color:#aaa;font-weight:600">NELER YAPABİLİRSİNİZ?</p>
                      <p style="margin:4px 0;font-size:13px;color:#888">🔍 Web araması ve güncel bilgiler</p>
                      <p style="margin:4px 0;font-size:13px;color:#888">📅 Google ve Outlook takvim entegrasyonu</p>
                      <p style="margin:4px 0;font-size:13px;color:#888">🎙️ Sesli komutlar</p>
                      <p style="margin:4px 0;font-size:13px;color:#888">📝 Not alma ve hatırlatıcılar</p>
                    </div>
                    <a href="https://aktivra.com" style="display:inline-block;padding:14px 28px;background:#fff;color:#0a0a0a;text-decoration:none;border-radius:12px;font-weight:700;font-size:14px">
                      Hemen Başlayın →
                    </a>
                  </div>
                  <div style="padding:16px 32px;border-top:1px solid #222;text-align:center">
                    <p style="margin:0;color:#555;font-size:11px">© 2026 Aktivra · Tüm hakları saklıdır.</p>
                  </div>
                </div>
                """
            })
        except Exception as e:
            print(f"Hosgeldin maili gonderilemedi: {e}")
        verify_url = f"https://aktivra.com/verify-email?token={token}"
        try:
            resend.Emails.send({
                "from": "Jarvis AI <noreply@aktivra.com>",
                "to": email,
                "subject": "E-posta adresinizi dogrulayin",
                "html": f"""
                <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#0a0a0a;color:#f0f0f0;border-radius:16px;overflow:hidden">
                  <div style="background:#111;padding:32px;text-align:center;border-bottom:1px solid #222">
                    <div style="width:48px;height:48px;background:#fff;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#0a0a0a;margin-bottom:12px">J</div>
                    <h1 style="margin:0;font-size:20px;font-weight:700;letter-spacing:.04em">JARVIS AI</h1>
                  </div>
                  <div style="padding:36px 32px">
                    <h2 style="margin:0 0 12px;font-size:18px;font-weight:600">Merhaba{', ' + isim if isim else ''}!</h2>
                    <p style="margin:0 0 24px;color:#888;font-size:14px;line-height:1.6">
                      Hesabinizi aktiflestirmek icin asagidaki butona tiklayin.<br>Bu link 24 saat gecerlidir.
                    </p>
                    <a href="{verify_url}" style="display:inline-block;padding:14px 28px;background:#fff;color:#0a0a0a;text-decoration:none;border-radius:12px;font-weight:700;font-size:14px">
                      E-postayi Dogrula
                    </a>
                    <p style="margin:24px 0 0;color:#555;font-size:12px">
                      Bu maili siz istemediyseniz dikkate almayin.
                    </p>
                  </div>
                </div>
                """
            })
        except Exception as e:
            print(f"Mail gonderilemedi: {e}")

    def register(self, email: str, isim: str, password: str) -> dict:
        try:
            db = SessionLocal()
            existing = db.execute(text("SELECT id FROM kullanicilar WHERE email = :e"), {"e": email}).fetchone()
            if existing:
                db.close()
                return {"error": "Bu email zaten kayitli"}
            sifre_hash = self.hash_password(password)
            result = db.execute(text(
                "INSERT INTO kullanicilar (email, isim, sifre_hash, email_verified) VALUES (:e, :i, :s, FALSE) RETURNING id"
            ), {"e": email, "i": isim, "s": sifre_hash})
            user_id = result.fetchone()[0]
            db.commit()

            verify_token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=24)
            db.execute(text(
                "INSERT INTO email_verification_tokens (kullanici_id, token, expires_at) VALUES (:u, :t, :e)"
            ), {"u": user_id, "t": verify_token, "e": expires})
            db.commit()
            db.close()

            self.send_verification_email(email, isim, verify_token)
            return {"success": True, "message": "Kayit basarili! Lutfen emailinizi dogrulayin."}
        except Exception as e:
            return {"error": str(e)}

    def verify_email(self, token: str) -> dict:
        try:
            db = SessionLocal()
            row = db.execute(text(
                "SELECT kullanici_id, expires_at FROM email_verification_tokens WHERE token = :t"
            ), {"t": token}).fetchone()
            if not row:
                db.close()
                return {"error": "Gecersiz veya kullanilmis dogrulama linki"}
            if row[1] < datetime.now():
                db.close()
                return {"error": "Dogrulama linkinin suresi dolmus. Lutfen tekrar kayit olun."}
            db.execute(text("UPDATE kullanicilar SET email_verified = TRUE WHERE id = :id"), {"id": row[0]})
            db.execute(text("DELETE FROM email_verification_tokens WHERE token = :t"), {"t": token})
            db.commit()
            session_token = self._create_session(db, row[0])
            user = db.execute(text("SELECT isim, email FROM kullanicilar WHERE id = :id"), {"id": row[0]}).fetchone()
            db.close()
            self.send_welcome_email(user[1], user[0])
            return {"success": True, "token": session_token, "user_id": row[0], "isim": user[0], "email": user[1]}
        except Exception as e:
            return {"error": str(e)}

    def login(self, email: str, password: str) -> dict:
        try:
            db = SessionLocal()
            user = db.execute(text(
                "SELECT id, isim, sifre_hash, avatar_url, email_verified FROM kullanicilar WHERE email = :e"
            ), {"e": email}).fetchone()
            if not user:
                db.close()
                return {"error": "Kullanici bulunamadi"}
            if not self.verify_password(password, user[2] or ""):
                db.close()
                return {"error": "Sifre yanlis"}
            if not user[4]:
                db.close()
                return {"error": "email_not_verified"}
            db.execute(text("UPDATE kullanicilar SET last_login = NOW() WHERE id = :id"), {"id": user[0]})
            db.commit()
            token = self._create_session(db, user[0])
            db.close()
            return {"token": token, "user_id": user[0], "isim": user[1], "email": email, "avatar_url": user[3]}
        except Exception as e:
            return {"error": str(e)}

    def resend_verification(self, email: str) -> dict:
        try:
            db = SessionLocal()
            user = db.execute(text(
                "SELECT id, isim, email_verified FROM kullanicilar WHERE email = :e"
            ), {"e": email}).fetchone()
            if not user:
                db.close()
                return {"error": "Bu email ile kayitli hesap bulunamadi"}
            if user[2]:
                db.close()
                return {"error": "Bu hesap zaten dogrulanmis"}
            db.execute(text("DELETE FROM email_verification_tokens WHERE kullanici_id = :id"), {"id": user[0]})
            verify_token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=24)
            db.execute(text(
                "INSERT INTO email_verification_tokens (kullanici_id, token, expires_at) VALUES (:u, :t, :e)"
            ), {"u": user[0], "t": verify_token, "e": expires})
            db.commit()
            db.close()
            self.send_verification_email(email, user[1], verify_token)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def oauth_login(self, email: str, isim: str, provider_id: str, provider: str, avatar_url: str = None) -> dict:
        try:
            db = SessionLocal()
            col = "google_id" if provider == "google" else "microsoft_id"
            user = db.execute(text("SELECT id, isim FROM kullanicilar WHERE email = :e"), {"e": email}).fetchone()
            if not user:
                result = db.execute(text(
                    f"INSERT INTO kullanicilar (email, isim, {col}, avatar_url, email_verified) VALUES (:e, :i, :p, :a, TRUE) RETURNING id, isim"
                ), {"e": email, "i": isim, "p": provider_id, "a": avatar_url})
                user = result.fetchone()
                db.commit()
                token = self._create_session(db, user[0])
                db.close()
                self.send_welcome_email(email, isim)
                return {"token": token, "user_id": user[0], "isim": user[1], "email": email, "avatar_url": avatar_url}
            else:
                db.execute(text(
                    f"UPDATE kullanicilar SET {col} = :p, last_login = NOW(), email_verified = TRUE WHERE id = :id"
                ), {"p": provider_id, "id": user[0]})
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
