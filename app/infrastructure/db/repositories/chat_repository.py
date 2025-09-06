from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.entities import ChatSession, Message
from app.domain.chat.repositories import ChatRepository
from app.infrastructure.db.models.chat_session import ChatSessionModel
from app.infrastructure.db.models.message import MessageModel


class SqlAlchemyChatRepository(ChatRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, user_id: UUID) -> ChatSession:
        model = ChatSessionModel(user_id=str(user_id), created_at=datetime.utcnow())
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ChatSession(id=UUID(model.id), user_id=UUID(model.user_id), created_at=model.created_at)

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
            return ChatSession(id=UUID(model.id), user_id=UUID(model.user_id), created_at=model.created_at)
        return None



