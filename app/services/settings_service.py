"""
FocuseMate – Settings Service
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings


async def get_user_settings(
    db: AsyncSession,
    user_id: int,
) -> UserSettings:
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        # Create default settings
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def update_user_settings(
    db: AsyncSession,
    user_id: int,
    notify_friend_requests: Optional[bool] = None,
    notify_room_invites: Optional[bool] = None,
    notify_messages: Optional[bool] = None,
    study_reminders: Optional[bool] = None,
    motivational_quotes: Optional[bool] = None,
    profile_visibility: Optional[str] = None,
    show_online_status: Optional[bool] = None,
    dark_mode: Optional[bool] = None,
) -> UserSettings:
    settings = await get_user_settings(db, user_id)

    if notify_friend_requests is not None:
        settings.notify_friend_requests = notify_friend_requests
    if notify_room_invites is not None:
        settings.notify_room_invites = notify_room_invites
    if notify_messages is not None:
        settings.notify_messages = notify_messages
    if study_reminders is not None:
        settings.study_reminders = study_reminders
    if motivational_quotes is not None:
        settings.motivational_quotes = motivational_quotes
    if profile_visibility is not None:
        settings.profile_visibility = profile_visibility
    if show_online_status is not None:
        settings.show_online_status = show_online_status
    if dark_mode is not None:
        settings.dark_mode = dark_mode

    await db.commit()
    await db.refresh(settings)
    return settings
