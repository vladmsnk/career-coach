from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, email: str, password_hash: str) -> User:
        raise NotImplementedError



