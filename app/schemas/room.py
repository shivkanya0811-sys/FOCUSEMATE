"""
FocuseMate – Room schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    max_members: int = Field(default=50, ge=2, le=500)


class RoomUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    max_members: Optional[int] = Field(None, ge=2, le=500)
    is_live: Optional[bool] = None


class RoomOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    owner_id: int
    is_live: bool = False
    focus: int = 0
    max_members: int = 50
    meeting_link: Optional[str] = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoomListOut(BaseModel):
    rooms: list[RoomOut]
    total: int


class RoomMemberOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class RoomMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(admin|member)$")


class MeetingCreate(BaseModel):
    room_id: Optional[int] = None
    title: Optional[str] = None
    start_time: Optional[datetime] = None


class MeetingOut(BaseModel):
    id: str
    meeting_link: str
    title: Optional[str] = None
    start_time: Optional[datetime] = None
