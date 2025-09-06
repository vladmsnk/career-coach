from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from .entities import ChatSession, Message


class ChatRepository(ABC):
    @abstractmethod
    async def create_session(self, user_id: UUID) -> ChatSession:
        raise NotImplementedError

    @abstractmethod
    async def add_message(self, session_id: UUID, role: str, content: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def list_messages(self, session_id: UUID) -> List[Message]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_session(self, user_id: UUID) -> ChatSession | None:
        raise NotImplementedError



