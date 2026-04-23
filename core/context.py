# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {"role": self.role, "content": self.content}


@dataclass
class ConversationContext:
    messages: List[Message] = field(default_factory=list)
    max_messages: int = 20

    def add(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def to_list(self) -> List[Dict]:
        return [m.to_dict() for m in self.messages]

    def last_n(self, n: int) -> List[Dict]:
        return [m.to_dict() for m in self.messages[-n:]]

    def clear(self):
        self.messages.clear()
