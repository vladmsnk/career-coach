from dataclasses import dataclass
from uuid import UUID

from app.domain.chat.repositories import ChatRepository


@dataclass
class StartChatSessionUseCase:
    chat_repository: ChatRepository

    async def execute(self, user_id: UUID) -> UUID:
        raise NotImplementedError



