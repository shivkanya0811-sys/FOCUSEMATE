"""
FocuseMate – Analytics schemas
"""
from __future__ import annotations

from pydantic import BaseModel


class RoomAnalytics(BaseModel):
    room_id: int
    room_title: str
    total_messages: int = 0
    total_resources: int = 0
    total_members: int = 0
    is_live: bool = False


class UserAnalytics(BaseModel):
    user_id: int
    rooms_joined: int = 0
    messages_sent: int = 0
    resources_added: int = 0
    friends_count: int = 0


class PlatformAnalytics(BaseModel):
    total_users: int = 0
    total_rooms: int = 0
    total_messages: int = 0
    total_resources: int = 0
    active_rooms: int = 0
