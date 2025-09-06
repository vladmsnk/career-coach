from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.entities import User
from app.domain.auth.repositories import UserRepository
from app.infrastructure.db.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    async def create(self, email: str, password_hash: str) -> User:
        raise NotImplementedError



