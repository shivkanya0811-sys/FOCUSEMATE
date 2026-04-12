"""
FocuseMate – Message schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    room_id: int
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: str = Field(default="text", pattern="^(text|link|code)$")


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListOut(BaseModel):
    messages: list[MessageOut]
    total: int
    has_more: bool = False
