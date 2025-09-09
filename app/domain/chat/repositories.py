from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities import ChatSession, Message


class ChatRepository(ABC):
    @abstractmethod
    async def create_session(
        self,
        user_id: UUID,
        *,
        status: str = "active",
        question_index: int = 0,
        answers_count: int = 0,
    ) -> ChatSession:
        raise NotImplementedError

    @abstractmethod
    async def add_message(self, session_id: UUID, role: str, content: str) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def list_messages(self, session_id: UUID) -> List[Message]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_session(self, user_id: UUID) -> Optional[ChatSession]:
        raise NotImplementedError

    @abstractmethod
    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        raise NotImplementedError

    @abstractmethod
    async def update_session(
        self,
        session_id: UUID,
        *,
        status: Optional[str] = None,
        question_index: Optional[int] = None,
        answers_count: Optional[int] = None,
    ) -> ChatSession:
        raise NotImplementedError

    @abstractmethod
    async def update_session_data(
        self,
        session_id: UUID,
        question_id: str,
        answer: str,
    ) -> None:
        """Update collected_data with new question-answer pair"""
        raise NotImplementedError



