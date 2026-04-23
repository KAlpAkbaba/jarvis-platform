# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Note(Base):
    __tablename__ = "notlar"
    id = Column(Integer, primary_key=True)
    content = Column("icerik", Text, nullable=False, key="icerik")
    category = Column("kategori", String(50), default="genel")
    created_at = Column("tarih", DateTime, default=datetime.now)
    remind_at = Column("hatirlatma", DateTime, nullable=True)
    completed = Column("tamamlandi", Boolean, default=False)


class Conversation(Base):
    __tablename__ = "konusmalar"
    id = Column(Integer, primary_key=True)
    role = Column("rol", String(20))
    content = Column("icerik", Text)
    created_at = Column("tarih", DateTime, default=datetime.now)


class Knowledge(Base):
    __tablename__ = "bilgiler"
    id = Column(Integer, primary_key=True)
    query = Column("sorgu", Text)
    answer = Column("yanit", Text)
    source = Column("kaynak", String(200), nullable=True)
    created_at = Column("tarih", DateTime, default=datetime.now)


class ArchivedNote(Base):
    __tablename__ = "gecmis_notlar"
    id = Column(Integer, primary_key=True)
    content = Column("icerik", Text, nullable=False)
    category = Column("kategori", String(50), default="genel")
    created_at = Column("olusturma", DateTime, default=datetime.now)
    remind_at = Column("hatirlatma", DateTime, nullable=True)
    archived_at = Column("tamamlanma", DateTime, default=datetime.now)


class Reservation(Base):
    __tablename__ = "rezervasyonlar"
    id = Column(Integer, primary_key=True)
    type = Column("tur", String(20))
    city = Column("sehir", String(100), nullable=True)
    from_city = Column("nereden", String(100), nullable=True)
    to_city = Column("nereye", String(100), nullable=True)
    check_in = Column("giris_tarihi", DateTime, nullable=True)
    check_out = Column("cikis_tarihi", DateTime, nullable=True)
    guests = Column("kisi", Integer, default=1)
    status = Column("durum", String(20), default="confirmed")
    details = Column("detaylar", Text, nullable=True)
    created_at = Column("tarih", DateTime, default=datetime.now)
