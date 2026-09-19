from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["user", "admin"]


class RegisterRequest(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=128)
    role: Role = "user"


class LoginRequest(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    role: Role


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
