from dataclasses import dataclass

from app.domain.auth.repositories import UserRepository


@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository

    async def execute(self, email: str, password: str) -> str:
        raise NotImplementedError



