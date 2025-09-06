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
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            return User(id=model.id, login=model.login, email=model.email, password_hash=model.password_hash)
        return None

    async def get_by_login(self, login: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.login == login)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            return User(id=model.id, login=model.login, email=model.email, password_hash=model.password_hash)
        return None

    async def create(self, login: str, email: str, password_hash: str) -> User:
        model = UserModel(login=login, email=email, password_hash=password_hash)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return User(id=model.id, login=model.login, email=model.email, password_hash=model.password_hash)



