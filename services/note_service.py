# -*- coding: utf-8 -*-
from datetime import datetime
from database.repository import add_note, get_notes, complete_note, get_archived_notes, time_expression


class NoteService:
    def add(self, content, category="genel", remind_at=None):
        add_note(content, category=category, remind_at=remind_at)
        return f"Not kaydedildi: {content}"

    def list(self, category=None):
        notes = get_notes(category)
        if not notes:
            return "Hic notunuz yok."
        result = "Notlariniz. "
        for i, (nid, content, cat, remind) in enumerate(notes, 1):
            result += f"{i}. {content}. "
        return result.strip()

    def list_reminders(self):
        notes = get_notes(category="hatirlatici")
        if not notes:
            return "Planlanmis hatirlatici yok."
        result = "Hatirlaticilariniz. "
        for i, (nid, content, cat, remind) in enumerate(notes, 1):
            zaman = time_expression(remind) if remind else "zamani belirsiz"
            result += f"{i}. {content}, {zaman}. "
        return result.strip()

    def list_archived(self):
        notes = get_archived_notes()
        if not notes:
            return "Gecmis notunuz yok."
        result = "Gecmis notlariniz. "
        for i, (nid, content, remind, archived) in enumerate(notes, 1):
            zaman = time_expression(remind) if remind else "zamani belirsiz"
            result += f"{i}. {content}, {zaman}. "
        return result.strip()

    def delete(self, note_id):
        complete_note(note_id)
        return f"{note_id} numarali notu sildim."

    def delete_last(self):
        notes = get_notes()
        if not notes:
            return "Silinecek not bulunamadi."
        last = notes[-1]
        complete_note(last[0])
        return f"Son notu sildim: {last[1]}"

    def get_all_ids(self):
        return [n[0] for n in get_notes()]
