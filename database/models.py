# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Note(Base):
    __tablename__ = "notlar"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="genel")
    created_at = Column(DateTime, default=datetime.now)
    remind_at = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)


class Conversation(Base):
    __tablename__ = "konusmalar"
    id = Column(Integer, primary_key=True)
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class Knowledge(Base):
    __tablename__ = "bilgiler"
    id = Column(Integer, primary_key=True)
    query = Column(Text)
    answer = Column(Text)
    source = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class ArchivedNote(Base):
    __tablename__ = "gecmis_notlar"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="genel")
    created_at = Column(DateTime, default=datetime.now)
    remind_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, default=datetime.now)


class Reservation(Base):
    __tablename__ = "rezervasyonlar"
    id = Column(Integer, primary_key=True)
    type = Column(String(20))
    city = Column(String(100), nullable=True)
    from_city = Column(String(100), nullable=True)
    to_city = Column(String(100), nullable=True)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    guests = Column(Integer, default=1)
    status = Column(String(20), default="confirmed")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)