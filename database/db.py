# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

DB_URL = "postgresql://postgres:***REMOVED***@postgres:5432/asistan"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(engine)
    print("Tablolar olusturuldu!")