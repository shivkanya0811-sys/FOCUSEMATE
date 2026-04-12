"""
FocuseMate – Notification Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListOut,
    NotificationMarkRead,
    NotificationOut,
)
from app.services.notification_service import (
    get_user_notifications,
    mark_all_read,
    mark_notifications_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListOut)
async def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notifications for the current user."""
    notifications, total, unread_count = await get_user_notifications(
        db, current_user.id, unread_only=unread_only, limit=limit, offset=offset
    )
    return NotificationListOut(
        notifications=[NotificationOut(**n) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


@router.post("/read", status_code=status.HTTP_200_OK)
async def mark_read(
    body: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark specific notifications as read."""
    count = await mark_notifications_read(db, current_user.id, body.notification_ids)
    return {"marked_read": count}


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    count = await mark_all_read(db, current_user.id)
    return {"marked_read": count}
