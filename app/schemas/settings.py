"""
FocuseMate – Settings schemas
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    notify_friend_requests: Optional[bool] = None
    notify_room_invites: Optional[bool] = None
    notify_messages: Optional[bool] = None
    study_reminders: Optional[bool] = None
    motivational_quotes: Optional[bool] = None
    profile_visibility: Optional[str] = Field(None, pattern="^(public|friends|private)$")
    show_online_status: Optional[bool] = None
    dark_mode: Optional[bool] = None


class SettingsOut(BaseModel):
    user_id: int
    notify_friend_requests: bool = True
    notify_room_invites: bool = True
    notify_messages: bool = True
    study_reminders: bool = True
    motivational_quotes: bool = True
    profile_visibility: str = "public"
    show_online_status: bool = True
    dark_mode: bool = False

    class Config:
        from_attributes = True
