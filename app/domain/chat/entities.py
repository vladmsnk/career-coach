from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ChatSession:
    id: UUID
    user_id: UUID
    created_at: datetime


@dataclass
class Message:
    id: UUID
    session_id: UUID
    role: str  # "user" or "bot"
    content: str
    created_at: datetime



