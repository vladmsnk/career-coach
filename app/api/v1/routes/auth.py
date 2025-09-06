from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    AuthTokenResponse,
)
from app.core.db import get_db_session
from app.domain.auth.repositories import UserRepository
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.auth.password import PasswordHasher
from app.infrastructure.auth.jwt import create_access_token
from app.application.auth.use_cases.register_user import RegisterUserUseCase
from app.application.auth.use_cases.authenticate_user import AuthenticateUserUseCase


router = APIRouter()


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return SqlAlchemyUserRepository(session)


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
async def register_user(
    payload: UserRegisterRequest, repo: UserRepository = Depends(get_user_repository)
) -> AuthTokenResponse:
    hasher = PasswordHasher()
    use_case = RegisterUserUseCase(user_repository=repo, password_hasher=hasher)
    try:
        user = await use_case.execute(payload.login, payload.email, payload.password)
    except ValueError:
        raise HTTPException(status_code=400, detail="User already exists")
    token = create_access_token(user.id)
    return AuthTokenResponse(access_token=token)


@router.post("/login", response_model=AuthTokenResponse)
async def login_user(
    payload: UserLoginRequest, repo: UserRepository = Depends(get_user_repository)
) -> AuthTokenResponse:
    hasher = PasswordHasher()
    use_case = AuthenticateUserUseCase(user_repository=repo, password_hasher=hasher)
    try:
        user = await use_case.execute(payload.login, payload.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return AuthTokenResponse(access_token=token)



