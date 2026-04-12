"""
FocuseMate – Auth schemas
"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str  # email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_data: "UserBrief"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserBrief(BaseModel):
    id: int
    name: str
    email: str
    avatar: str | None = None
    level: int = 1
    xp: int = 0

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
