from dataclasses import dataclass

from app.domain.auth.entities import User
from app.domain.auth.repositories import UserRepository
from app.infrastructure.auth.password import PasswordHasher


@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, login: str, email: str, password: str) -> User:
        if await self.user_repository.get_by_email(email) or await self.user_repository.get_by_login(login):
            raise ValueError("User already exists")
        password_hash = self.password_hasher.hash(password)
        return await self.user_repository.create(login=login, email=email, password_hash=password_hash)



