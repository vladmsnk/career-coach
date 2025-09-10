import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from app.infrastructure.db.base import Base


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_module: Mapped[str] = mapped_column(String(20), nullable=False, default="current_profile")
    collected_data: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False, default=dict)



