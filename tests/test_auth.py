import os
import sys
import asyncio
import pytest
from fastapi import HTTPException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.v1.routes.auth import register_user, login_user
from app.domain.auth.entities import User
from app.domain.auth.repositories import UserRepository
from app.schemas.auth import UserRegisterRequest, UserLoginRequest


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get_by_login(self, login: str) -> User | None:
        return self.users.get(login)

    async def create(self, login: str, email: str, password_hash: str) -> User:
        user = User(id=login, login=login, email=email, password_hash=password_hash)
        self.users[login] = user
        return user


def test_register_and_login():
    repo = InMemoryUserRepository()
    response = asyncio.run(
        register_user(
            UserRegisterRequest(login="user1", email="user1@example.com", password="secret"),
            repo=repo,
        )
    )
    assert response.access_token

    response = asyncio.run(
        login_user(
            UserLoginRequest(login="user1", password="secret"),
            repo=repo,
        )
    )
    assert response.access_token


def test_login_wrong_password():
    repo = InMemoryUserRepository()
    asyncio.run(
        register_user(
            UserRegisterRequest(login="user2", email="user2@example.com", password="secret"),
            repo=repo,
        )
    )
    with pytest.raises(HTTPException):
        asyncio.run(
            login_user(
                UserLoginRequest(login="user2", password="wrong"),
                repo=repo,
            )
        )
