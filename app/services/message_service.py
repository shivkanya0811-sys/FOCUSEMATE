"""
FocuseMate – Message Service
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageType
from app.models.user import User


async def create_message(
    db: AsyncSession,
    room_id: int,
    sender_id: int,
    content: str,
    message_type: str = "text",
) -> dict:
    msg = Message(
        room_id=room_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Fetch sender info
    result = await db.execute(select(User).where(User.id == sender_id))
    sender = result.scalar_one_or_none()

    return {
        "id": msg.id,
        "room_id": msg.room_id,
        "sender_id": msg.sender_id,
        "sender_name": sender.name if sender else None,
        "sender_avatar": sender.avatar if sender else None,
        "content": msg.content,
        "message_type": msg.message_type,
        "created_at": msg.created_at,
    }


async def get_room_messages(
    db: AsyncSession,
    room_id: int,
    limit: int = 50,
    offset: int = 0,
    before_id: int | None = None,
) -> tuple[list[dict], int, bool]:
    """Fetch paginated messages for a room, ordered newest first."""
    count_query = select(func.count(Message.id)).where(Message.room_id == room_id)
    if before_id:
        count_query = count_query.where(Message.id < before_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(Message, User)
        .outerjoin(User, Message.sender_id == User.id)
        .where(Message.room_id == room_id)
    )
    if before_id:
        query = query.where(Message.id < before_id)

    query = query.order_by(Message.created_at.desc()).offset(offset).limit(limit + 1)
    result = await db.execute(query)
    rows = result.all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    messages = [
        {
            "id": msg.id,
            "room_id": msg.room_id,
            "sender_id": msg.sender_id,
            "sender_name": u.name if u else None,
            "sender_avatar": u.avatar if u else None,
            "content": msg.content,
            "message_type": msg.message_type,
            "created_at": msg.created_at,
        }
        for msg, u in rows
    ]
    return messages, total, has_more
