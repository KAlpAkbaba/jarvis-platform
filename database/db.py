# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

import core.config  # noqa: F401  (.env dosyasini yukler)

DB_URL = os.environ['DATABASE_URL']

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