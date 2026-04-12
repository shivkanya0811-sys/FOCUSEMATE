"""
FocuseMate – Notification Service
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    user_id: int,
    notification_type: str,
    title: str,
    body: Optional[str] = None,
    actor_id: Optional[int] = None,
    reference_id: Optional[int] = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        actor_id=actor_id,
        notification_type=notification_type,
        title=title,
        body=body,
        reference_id=reference_id,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def get_user_notifications(
    db: AsyncSession,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int, int]:
    """Return notifications with total and unread count."""
    # Unread count
    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    unread_count = unread_result.scalar() or 0

    # Total count
    count_query = select(func.count(Notification.id)).where(
        Notification.user_id == user_id
    )
    if unread_only:
        count_query = count_query.where(Notification.is_read == False)  # noqa: E712
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch
    query = (
        select(Notification, User)
        .outerjoin(User, Notification.actor_id == User.id)
        .where(Notification.user_id == user_id)
    )
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    result = await db.execute(
        query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    notifications = [
        {
            "id": n.id,
            "user_id": n.user_id,
            "actor_id": n.actor_id,
            "actor_name": u.name if u else None,
            "notification_type": n.notification_type,
            "title": n.title,
            "body": n.body,
            "reference_id": n.reference_id,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n, u in rows
    ]
    return notifications, total, unread_count


async def mark_notifications_read(
    db: AsyncSession,
    user_id: int,
    notification_ids: list[int],
) -> int:
    """Mark specific notifications as read. Returns number updated."""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids),
        )
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount


async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount
