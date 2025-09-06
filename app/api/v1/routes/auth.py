from fastapi import APIRouter, HTTPException

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    AuthTokenResponse,
)


router = APIRouter()


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
async def register_user(payload: UserRegisterRequest) -> AuthTokenResponse:
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/login", response_model=AuthTokenResponse)
async def login_user(payload: UserLoginRequest) -> AuthTokenResponse:
    raise HTTPException(status_code=501, detail="Not implemented")



