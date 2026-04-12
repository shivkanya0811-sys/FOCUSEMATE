"""
FocuseMate – Settings Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.settings import SettingsOut, SettingsUpdate
from app.services.settings_service import get_user_settings, update_user_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=SettingsOut)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's settings."""
    settings = await get_user_settings(db, current_user.id)
    return SettingsOut.model_validate(settings)


@router.patch("/", response_model=SettingsOut)
async def update_settings(
    body: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's settings."""
    settings = await update_user_settings(
        db,
        current_user.id,
        notify_friend_requests=body.notify_friend_requests,
        notify_room_invites=body.notify_room_invites,
        notify_messages=body.notify_messages,
        study_reminders=body.study_reminders,
        motivational_quotes=body.motivational_quotes,
        profile_visibility=body.profile_visibility,
        show_online_status=body.show_online_status,
        dark_mode=body.dark_mode,
    )
    return SettingsOut.model_validate(settings)
