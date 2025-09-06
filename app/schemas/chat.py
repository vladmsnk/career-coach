from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StartChatSessionRequest(BaseModel):
    user_id: UUID


class StartChatSessionResponse(BaseModel):
    session_id: UUID
    created_at: datetime


class SubmitMessageRequest(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    message_id: UUID
    session_id: UUID
    content: str
    role: str
    created_at: datetime


class BotQuestionResponse(BaseModel):
    session_id: UUID
    question: str
    context: Optional[dict] = None



