"""
FocuseMate – Notification schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    notification_type: str
    title: str
    body: Optional[str] = None
    reference_id: Optional[int] = None
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListOut(BaseModel):
    notifications: list[NotificationOut]
    total: int
    unread_count: int = 0


class NotificationMarkRead(BaseModel):
    notification_ids: list[int]
