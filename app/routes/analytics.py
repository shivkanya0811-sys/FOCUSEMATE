"""
FocuseMate – Analytics Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import PlatformAnalytics, RoomAnalytics, UserAnalytics
from app.services.analytics_service import (
    get_platform_analytics,
    get_room_analytics,
    get_user_analytics,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/me", response_model=UserAnalytics)
async def my_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for the current user."""
    data = await get_user_analytics(db, current_user.id)
    return UserAnalytics(**data)


@router.get("/rooms/{room_id}", response_model=RoomAnalytics)
async def room_analytics(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for a specific room."""
    try:
        data = await get_room_analytics(db, room_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return RoomAnalytics(**data)


@router.get("/platform", response_model=PlatformAnalytics)
async def platform_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get platform-wide analytics (admin or any authenticated user)."""
    data = await get_platform_analytics(db)
    return PlatformAnalytics(**data)
