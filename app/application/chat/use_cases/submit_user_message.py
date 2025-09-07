from dataclasses import dataclass
from uuid import UUID

from app.domain.chat.entities import Message
from app.domain.chat.repositories import ChatRepository


@dataclass
class SubmitUserMessageUseCase:
    chat_repository: ChatRepository

    async def execute(self, session_id: UUID, content: str) -> Message:
        message = await self.chat_repository.add_message(session_id, "user", content)
        session = await self.chat_repository.get_session(session_id)
        await self.chat_repository.update_session(
            session_id, answers_count=session.answers_count + 1
        )
        return message



