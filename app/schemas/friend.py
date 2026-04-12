"""
FocuseMate – Friend schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FriendRequestCreate(BaseModel):
    receiver_id: int


class FriendRequestOut(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    sender_avatar: Optional[str] = None
    receiver_id: int
    receiver_name: str
    receiver_avatar: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FriendRequestAction(BaseModel):
    action: str = Field(..., pattern="^(accept|reject)$")


class FriendOut(BaseModel):
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    level: int = 1
    xp: int = 0

    class Config:
        from_attributes = True


class FriendListOut(BaseModel):
    friends: list[FriendOut]
    total: int
