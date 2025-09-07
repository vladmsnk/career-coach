from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.chat.repositories import ChatRepository
from app.domain.chat.questions import QUESTIONS


@dataclass
class StartChatSessionUseCase:
    chat_repository: ChatRepository

    async def execute(self, user_id: UUID) -> tuple[UUID, str, datetime]:
        session = await self.chat_repository.get_latest_session(user_id)
        if session and session.status == "active" and session.answers_count < len(QUESTIONS):
            question = QUESTIONS[session.question_index]["prompt"]
            return session.id, question, session.created_at
        session = await self.chat_repository.create_session(user_id, question_index=1)
        question = QUESTIONS[0]["prompt"]
        return session.id, question, session.created_at



