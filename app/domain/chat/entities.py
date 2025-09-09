from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from typing import Dict, Any


@dataclass
class ChatSession:
    id: UUID
    user_id: UUID
    created_at: datetime
    status: str
    question_index: int
    answers_count: int
    current_module: str = "context"
    collected_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    id: UUID
    session_id: UUID
    role: str  # "user" or "bot"
    content: str
    created_at: datetime



