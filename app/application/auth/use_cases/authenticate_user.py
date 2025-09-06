from dataclasses import dataclass

from app.domain.auth.entities import User
from app.domain.auth.repositories import UserRepository
from app.infrastructure.auth.password import PasswordHasher


@dataclass
class AuthenticateUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, login: str, password: str) -> User:
        user = await self.user_repository.get_by_login(login)
        if not user or not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Invalid credentials")
        return user



