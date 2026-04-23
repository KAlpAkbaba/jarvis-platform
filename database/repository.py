# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from database.models import Note, Conversation, Knowledge, ArchivedNote, Reservation
from database.db import SessionLocal


def _db():
    return SessionLocal()


def add_note(content, category="genel", remind_at=None):
    db = _db()
    note = Note(content=content, category=category, remind_at=remind_at)
    db.add(note)
    db.commit()
    note_id = note.id
    db.close()
    return note_id


def get_notes(category=None):
    db = _db()
    q = db.query(Note).filter_by(completed=False)
    if category:
        q = q.filter_by(category=category)
    notes = [(n.id, n.content, n.category, n.remind_at) for n in q.all()]
    db.close()
    return notes


def complete_note(note_id):
    db = _db()
    note = db.query(Note).filter_by(id=note_id).first()
    if note:
        note.completed = True
        db.commit()
    db.close()


def archive_note(note_id):
    db = _db()
    note = db.query(Note).filter_by(id=note_id).first()
    if note:
        archived = ArchivedNote(
            content=note.content, category=note.category,
            created_at=note.created_at, remind_at=note.remind_at,
            archived_at=datetime.now()
        )
        db.add(archived)
        note.completed = True
        db.commit()
    db.close()


def get_archived_notes(limit=10):
    db = _db()
    notes = db.query(ArchivedNote).order_by(ArchivedNote.archived_at.desc()).limit(limit).all()
    result = [(n.id, n.content, n.remind_at, n.archived_at) for n in notes]
    db.close()
    return result


def get_pending_reminders():
    db = _db()
    now = datetime.now()
    notify_time = now + timedelta(minutes=15)
    notes = db.query(Note).filter(
        Note.category == "hatirlatici",
        Note.completed == False,
        Note.remind_at <= notify_time,
        Note.remind_at >= now - timedelta(minutes=1)
    ).all()
    result = [(n.id, n.content, n.remind_at) for n in notes]
    db.close()
    return result


def archive_expired_reminders():
    db = _db()
    now = datetime.now()
    expired = db.query(Note).filter(
        Note.category == "hatirlatici",
        Note.completed == False,
        Note.remind_at < now - timedelta(hours=1)
    ).all()
    for note in expired:
        archived = ArchivedNote(
            content=note.content, category=note.category,
            created_at=note.created_at, remind_at=note.remind_at,
            archived_at=now
        )
        db.add(archived)
        note.completed = True
    db.commit()
    db.close()


def save_conversation(role, content):
    db = _db()
    db.add(Conversation(role=role, content=content))
    db.commit()
    db.close()


def get_recent_conversations(limit=20):
    db = _db()
    records = db.query(Conversation).order_by(Conversation.created_at.desc()).limit(limit).all()
    result = [{"role": r.role, "content": r.content} for r in reversed(records)]
    db.close()
    return result


def save_knowledge(query, answer, source=None):
    db = _db()
    db.add(Knowledge(query=query, answer=answer, source=source))
    db.commit()
    db.close()


def search_knowledge(query):
    db = _db()
    item = db.query(Knowledge).filter(
        Knowledge.query.ilike(f"%{query}%")
    ).order_by(Knowledge.created_at.desc()).first()
    result = {"query": item.query, "answer": item.answer} if item else None
    db.close()
    return result


def save_reservation(type, city=None, from_city=None, to_city=None,
                     check_in=None, check_out=None, guests=1, details=None):
    db = _db()
    rez = Reservation(
        type=type, city=city, from_city=from_city, to_city=to_city,
        check_in=check_in, check_out=check_out, guests=guests,
        details=json.dumps(details, ensure_ascii=False) if details else None
    )
    db.add(rez)
    db.commit()
    rez_id = rez.id
    db.close()
    return rez_id


def get_reservations(type=None, limit=10):
    db = _db()
    q = db.query(Reservation).filter_by(status="confirmed")
    if type:
        q = q.filter_by(type=type)
    records = q.order_by(Reservation.created_at.desc()).limit(limit).all()
    result = [{
        "id": r.id, "type": r.type, "city": r.city,
        "from_city": r.from_city, "to_city": r.to_city,
        "check_in": r.check_in, "check_out": r.check_out,
        "guests": r.guests
    } for r in records]
    db.close()
    return result


def time_expression(target):
    now = datetime.now()
    diff_seconds = (target - now).total_seconds()
    diff_days = (target.date() - now.date()).days

    if diff_seconds < 0:
        elapsed = abs(diff_seconds)
        if elapsed < 3600:
            return f"{int(elapsed/60)} dakika once"
        elif elapsed < 86400:
            return f"{int(elapsed/3600)} saat once"
        elif diff_days == -1:
            return f"dun saat {target.strftime('%H:%M')}"
        else:
            return f"{abs(diff_days)} gun once"
    else:
        if diff_days == 0:
            return f"bugun saat {target.strftime('%H:%M')}"
        elif diff_days == 1:
            return f"yarin saat {target.strftime('%H:%M')}"
        elif diff_days < 7:
            return f"{diff_days} gun sonra saat {target.strftime('%H:%M')}"
        elif diff_days < 30:
            return f"{diff_days//7} hafta sonra"
        else:
            return f"{diff_days//30} ay sonra"