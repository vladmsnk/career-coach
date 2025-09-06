from dataclasses import dataclass
from uuid import UUID

from app.domain.chat.repositories import ChatRepository


@dataclass
class SubmitUserMessageUseCase:
    chat_repository: ChatRepository

    async def execute(self, session_id: UUID, content: str) -> UUID:
        raise NotImplementedError



