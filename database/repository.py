from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import json

DB_URL = "postgresql://postgres:***REMOVED***@localhost:5432/asistan"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# ============ TABLOLAR ============

class Not(Base):
    __tablename__ = "notlar"
    id         = Column(Integer, primary_key=True)
    içerik     = Column(Text, nullable=False)
    kategori   = Column(String(50), default="genel")
    tarih      = Column(DateTime, default=datetime.now)
    hatırlatma = Column(DateTime, nullable=True)
    tamamlandı = Column(Boolean, default=False)


class Konuşma(Base):
    __tablename__ = "konusmalar"
    id     = Column(Integer, primary_key=True)
    rol    = Column(String(20))
    içerik = Column(Text)
    tarih  = Column(DateTime, default=datetime.now)


class Bilgi(Base):
    __tablename__ = "bilgiler"
    id     = Column(Integer, primary_key=True)
    sorgu  = Column(Text)
    yanıt  = Column(Text)
    kaynak = Column(String(200), nullable=True)
    tarih  = Column(DateTime, default=datetime.now)


class GecmisNot(Base):
    __tablename__ = "gecmis_notlar"
    id         = Column(Integer, primary_key=True)
    içerik     = Column(Text, nullable=False)
    kategori   = Column(String(50), default="genel")
    oluşturma  = Column(DateTime, default=datetime.now)
    hatırlatma = Column(DateTime, nullable=True)
    tamamlanma = Column(DateTime, default=datetime.now)


class Rezervasyon(Base):
    __tablename__ = "rezervasyonlar"
    id           = Column(Integer, primary_key=True)
    tür          = Column(String(20))
    şehir        = Column(String(100), nullable=True)
    nereden      = Column(String(100), nullable=True)
    nereye       = Column(String(100), nullable=True)
    giriş_tarihi = Column(DateTime, nullable=True)
    çıkış_tarihi = Column(DateTime, nullable=True)
    kişi         = Column(Integer, default=1)
    durum        = Column(String(20), default="onaylandı")
    detaylar     = Column(Text, nullable=True)
    tarih        = Column(DateTime, default=datetime.now)


def tabloları_oluştur():
    Base.metadata.create_all(engine)
    print("✅ Tablolar oluşturuldu!")


# ============ NOT FONKSİYONLARI ============

def not_ekle(içerik: str, kategori: str = "genel", hatırlatma: datetime = None):
    session = Session()
    yeni_not = Not(içerik=içerik, kategori=kategori, hatırlatma=hatırlatma)
    session.add(yeni_not)
    session.commit()
    session.close()
    return "Not kaydedildi."


def notları_getir(kategori: str = None):
    session = Session()
    if kategori:
        notlar = session.query(Not).filter_by(kategori=kategori, tamamlandı=False).all()
    else:
        notlar = session.query(Not).filter_by(tamamlandı=False).all()
    sonuç = [(n.id, n.içerik, n.kategori, n.hatırlatma) for n in notlar]
    session.close()
    return sonuç


def notu_tamamla(not_id: int):
    session = Session()
    not_ = session.query(Not).filter_by(id=not_id).first()
    if not_:
        not_.tamamlandı = True
        session.commit()
    session.close()


def notu_arsivle(not_id: int):
    session = Session()
    not_ = session.query(Not).filter_by(id=not_id).first()
    if not_:
        gecmis = GecmisNot(
            içerik=not_.içerik,
            kategori=not_.kategori,
            oluşturma=not_.tarih,
            hatırlatma=not_.hatırlatma,
            tamamlanma=datetime.now()
        )
        session.add(gecmis)
        not_.tamamlandı = True
        session.commit()
    session.close()


def gecmis_notlari_getir(limit: int = 10) -> list:
    session = Session()
    notlar = session.query(GecmisNot).order_by(
        GecmisNot.tamamlanma.desc()
    ).limit(limit).all()
    sonuç = [(n.id, n.içerik, n.hatırlatma, n.tamamlanma) for n in notlar]
    session.close()
    return sonuç


# ============ KONUŞMA FONKSİYONLARI ============

def konuşma_kaydet(rol: str, içerik: str):
    session = Session()
    kayıt = Konuşma(rol=rol, içerik=içerik)
    session.add(kayıt)
    session.commit()
    session.close()


def son_konuşmaları_getir(limit: int = 20):
    session = Session()
    kayıtlar = session.query(Konuşma).order_by(
        Konuşma.tarih.desc()
    ).limit(limit).all()
    sonuç = [{"rol": k.rol, "içerik": k.içerik} for k in kayıtlar]
    session.close()
    return list(reversed(sonuç))


# ============ BİLGİ FONKSİYONLARI ============

def bilgi_kaydet(sorgu: str, yanıt: str, kaynak: str = None):
    session = Session()
    bilgi = Bilgi(sorgu=sorgu, yanıt=yanıt, kaynak=kaynak)
    session.add(bilgi)
    session.commit()
    session.close()


def bilgi_ara(sorgu: str):
    session = Session()
    bilgi = session.query(Bilgi).filter(
        Bilgi.sorgu.ilike(f"%{sorgu}%")
    ).order_by(Bilgi.tarih.desc()).first()
    sonuç = {"sorgu": bilgi.sorgu, "yanıt": bilgi.yanıt} if bilgi else None
    session.close()
    return sonuç


# ============ ZAMAN FONKSİYONLARI ============

def zaman_ifadesi(hedef: datetime) -> str:
    şimdi = datetime.now()
    fark = hedef - şimdi
    fark_saniye = fark.total_seconds()
    hedef_gun = hedef.date()
    bugun = şimdi.date()
    fark_gun_sayisi = (hedef_gun - bugun).days

    if fark_saniye < 0:
        gecen = abs(fark_saniye)
        if gecen < 3600:
            return f"{int(gecen/60)} dakika önce"
        elif gecen < 86400:
            return f"{int(gecen/3600)} saat önce"
        elif fark_gun_sayisi == -1:
            return f"dün saat {hedef.strftime('%H:%M')}"
        elif abs(fark_gun_sayisi) < 7:
            return f"{abs(fark_gun_sayisi)} gün önce saat {hedef.strftime('%H:%M')}"
        elif abs(fark_gun_sayisi) < 30:
            return f"{abs(fark_gun_sayisi)//7} hafta önce"
        elif abs(fark_gun_sayisi) < 365:
            return f"{abs(fark_gun_sayisi)//30} ay önce"
        else:
            return f"{abs(fark_gun_sayisi)//365} yıl önce"
    else:
        if fark_gun_sayisi == 0:
            return f"bugün saat {hedef.strftime('%H:%M')}"
        elif fark_gun_sayisi == 1:
            return f"yarın saat {hedef.strftime('%H:%M')}"
        elif fark_gun_sayisi == 2:
            return f"öbür gün saat {hedef.strftime('%H:%M')}"
        elif fark_gun_sayisi < 7:
            return f"{fark_gun_sayisi} gün sonra saat {hedef.strftime('%H:%M')}"
        elif fark_gun_sayisi < 30:
            return f"{fark_gun_sayisi//7} hafta sonra"
        elif fark_gun_sayisi < 365:
            return f"{fark_gun_sayisi//30} ay sonra"
        else:
            return f"{fark_gun_sayisi//365} yıl sonra"


# ============ HATIRLATICI FONKSİYONLARI ============

def hatırlatıcıları_kontrol_et() -> list:
    session = Session()
    şimdi = datetime.now()
    bildirim_zamanı = şimdi + timedelta(minutes=15)

    notlar = session.query(Not).filter(
        Not.kategori == "hatırlatıcı",
        Not.tamamlandı == False,
        Not.hatırlatma <= bildirim_zamanı,
        Not.hatırlatma >= şimdi - timedelta(minutes=1)
    ).all()

    sonuç = [(n.id, n.içerik, n.hatırlatma) for n in notlar]
    session.close()
    return sonuç


def zamani_gecen_notlari_arsivle():
    session = Session()
    şimdi = datetime.now()

    gecmis = session.query(Not).filter(
        Not.kategori == "hatırlatıcı",
        Not.tamamlandı == False,
        Not.hatırlatma < şimdi - timedelta(hours=1)
    ).all()

    for not_ in gecmis:
        gecmis_not = GecmisNot(
            içerik=not_.içerik,
            kategori=not_.kategori,
            oluşturma=not_.tarih,
            hatırlatma=not_.hatırlatma,
            tamamlanma=şimdi
        )
        session.add(gecmis_not)
        not_.tamamlandı = True

    session.commit()
    session.close()


# ============ REZERVASYON FONKSİYONLARI ============

def rezervasyon_kaydet(tür, şehir=None, nereden=None, nereye=None,
                        giriş=None, çıkış=None, kişi=1, detaylar=None):
    session = Session()
    rez = Rezervasyon(
        tür=tür,
        şehir=şehir,
        nereden=nereden,
        nereye=nereye,
        giriş_tarihi=giriş,
        çıkış_tarihi=çıkış,
        kişi=kişi,
        detaylar=json.dumps(detaylar, ensure_ascii=False) if detaylar else None
    )
    session.add(rez)
    session.commit()
    rez_id = rez.id
    session.close()
    return rez_id


def rezervasyonları_getir(tür=None, limit=10):
    session = Session()
    q = session.query(Rezervasyon).filter_by(durum="onaylandı")
    if tür:
        q = q.filter_by(tür=tür)
    sonuçlar = q.order_by(Rezervasyon.tarih.desc()).limit(limit).all()
    liste = [{
        "id": r.id,
        "tür": r.tür,
        "şehir": r.şehir,
        "nereden": r.nereden,
        "nereye": r.nereye,
        "giriş": r.giriş_tarihi,
        "çıkış": r.çıkış_tarihi,
        "kişi": r.kişi
    } for r in sonuçlar]
    session.close()
    return liste


def son_rezervasyonu_getir(tür=None):
    liste = rezervasyonları_getir(tür=tür, limit=1)
    return liste[0] if liste else None


# ============ TEST ============

if __name__ == "__main__":
    tabloları_oluştur()

    not_ekle("Yarın saat 15'te toplantı var", kategori="hatırlatıcı")
    not_ekle("Market: süt, ekmek, yumurta", kategori="alışveriş")

    notlar = notları_getir()
    print("\n📝 Notlar:")
    for n in notlar:
        print(f"  [{n[0]}] {n[1]} ({n[2]})")

    konuşma_kaydet("user", "Merhaba!")
    konuşma_kaydet("assistant", "Merhaba! Nasıl yardımcı olabilirim?")

    print("\n💬 Son konuşmalar:")
    for k in son_konuşmaları_getir():
        print(f"  {k['rol']}: {k['içerik']}")

    print("\n✅ Tüm testler başarılı!")