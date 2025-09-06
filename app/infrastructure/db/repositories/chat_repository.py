from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.entities import ChatSession, Message
from app.domain.chat.repositories import ChatRepository


class SqlAlchemyChatRepository(ChatRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, user_id: UUID) -> ChatSession:
        raise NotImplementedError

    async def add_message(self, session_id: UUID, role: str, content: str) -> Message:
        raise NotImplementedError

    async def list_messages(self, session_id: UUID) -> List[Message]:
        raise NotImplementedError



