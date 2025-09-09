from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.entities import ChatSession, Message
from app.domain.chat.repositories import ChatRepository
from app.infrastructure.db.models.chat_session import ChatSessionModel
from app.infrastructure.db.models.message import MessageModel


class SqlAlchemyChatRepository(ChatRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        user_id: UUID,
        *,
        status: str = "active",
        question_index: int = 0,
        answers_count: int = 0,
    ) -> ChatSession:
        model = ChatSessionModel(
            user_id=str(user_id),
            created_at=datetime.utcnow(),
            status=status,
            question_index=question_index,
            answers_count=answers_count,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ChatSession(
            id=UUID(model.id),
            user_id=UUID(model.user_id),
            created_at=model.created_at,
            status=model.status,
            question_index=model.question_index,
            answers_count=model.answers_count,
        )

    async def add_message(self, session_id: UUID, role: str, content: str) -> Message:
        model = MessageModel(
            session_id=str(session_id),
            role=role,
            content=content,
            created_at=datetime.utcnow(),
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return Message(
            id=UUID(model.id),
            session_id=UUID(model.session_id),
            role=model.role,
            content=model.content,
            created_at=model.created_at,
        )

    async def list_messages(self, session_id: UUID) -> List[Message]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == str(session_id))
            .order_by(MessageModel.created_at)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [
            Message(
                id=UUID(m.id),
                session_id=UUID(m.session_id),
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def get_latest_session(self, user_id: UUID) -> Optional[ChatSession]:
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.user_id == str(user_id))
            .order_by(ChatSessionModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            return ChatSession(
                id=UUID(model.id),
                user_id=UUID(model.user_id),
                created_at=model.created_at,
                status=model.status,
                question_index=model.question_index,
                answers_count=model.answers_count,
                current_module=model.current_module,
                collected_data=model.collected_data,
            )
        return None

    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == str(session_id))
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            return ChatSession(
                id=UUID(model.id),
                user_id=UUID(model.user_id),
                created_at=model.created_at,
                status=model.status,
                question_index=model.question_index,
                answers_count=model.answers_count,
                current_module=model.current_module,
                collected_data=model.collected_data,
            )
        return None

    async def update_session(
        self,
        session_id: UUID,
        *,
        status: Optional[str] = None,
        question_index: Optional[int] = None,
        answers_count: Optional[int] = None,
    ) -> ChatSession:
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == str(session_id))
        result = await self._session.execute(stmt)
        model = result.scalars().one()
        if status is not None:
            model.status = status
        if question_index is not None:
            model.question_index = question_index
        if answers_count is not None:
            model.answers_count = answers_count
        await self._session.commit()
        await self._session.refresh(model)
        return ChatSession(
            id=UUID(model.id),
            user_id=UUID(model.user_id),
            created_at=model.created_at,
            status=model.status,
            question_index=model.question_index,
            answers_count=model.answers_count,
            current_module=model.current_module,
            collected_data=model.collected_data,
        )

    async def update_session_data(
        self,
        session_id: UUID,
        question_id: str,
        answer: str,
    ) -> None:
        """Update collected_data with new question-answer pair"""
        # Get current session
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == str(session_id))
        result = await self._session.execute(stmt)
        model = result.scalars().one()
        
        # Update collected_data
        current_data = model.collected_data or {}
        current_data[question_id] = answer
        model.collected_data = current_data
        
        await self._session.commit()



