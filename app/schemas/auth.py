from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    login: str
    email: str
    password: str


class UserLoginRequest(BaseModel):
    login: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"



