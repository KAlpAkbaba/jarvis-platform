# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from core.context import ConversationContext


@dataclass
class Session:
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    context: ConversationContext = field(default_factory=ConversationContext)
    dialog_state: Dict[str, Any] = field(default_factory=lambda: {
        "active": False, "step": None, "data": {}
    })

    def reset_dialog(self):
        self.dialog_state = {"active": False, "step": None, "data": {}}

    def is_dialog_active(self):
        return self.dialog_state.get("active", False)


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
        return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str):
        self._sessions.pop(session_id, None)


session_manager = SessionManager()
