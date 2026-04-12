"""
FocuseMate – User schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    level: int = 1
    xp: int = 0
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    bio: Optional[str] = Field(None, max_length=500)
    avatar: Optional[str] = Field(None, max_length=512)


class UserSearch(BaseModel):
    query: str = Field(..., min_length=1, max_length=120)


class UserListOut(BaseModel):
    users: list[UserOut]
    total: int
