"""
FocuseMate – Analytics Service
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friend_request import FriendRequest, FriendStatus
from app.models.message import Message
from app.models.resource import Resource
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User


async def get_room_analytics(
    db: AsyncSession,
    room_id: int,
) -> dict:
    room_result = await db.execute(select(Room).where(Room.id == room_id))
    room = room_result.scalar_one_or_none()
    if not room:
        raise ValueError("Room not found")

    msg_count = await db.execute(
        select(func.count(Message.id)).where(Message.room_id == room_id)
    )
    res_count = await db.execute(
        select(func.count(Resource.id)).where(Resource.room_id == room_id)
    )
    member_count = await db.execute(
        select(func.count(RoomMember.id)).where(RoomMember.room_id == room_id)
    )

    return {
        "room_id": room.id,
        "room_title": room.title,
        "total_messages": msg_count.scalar() or 0,
        "total_resources": res_count.scalar() or 0,
        "total_members": member_count.scalar() or 0,
        "is_live": room.is_live,
    }


async def get_user_analytics(
    db: AsyncSession,
    user_id: int,
) -> dict:
    rooms_joined = await db.execute(
        select(func.count(RoomMember.id)).where(RoomMember.user_id == user_id)
    )
    messages_sent = await db.execute(
        select(func.count(Message.id)).where(Message.sender_id == user_id)
    )
    resources_added = await db.execute(
        select(func.count(Resource.id)).where(Resource.added_by == user_id)
    )
    friends_count = await db.execute(
        select(func.count(FriendRequest.id)).where(
            FriendRequest.status == FriendStatus.ACCEPTED.value,
            (FriendRequest.sender_id == user_id) | (FriendRequest.receiver_id == user_id),
        )
    )

    return {
        "user_id": user_id,
        "rooms_joined": rooms_joined.scalar() or 0,
        "messages_sent": messages_sent.scalar() or 0,
        "resources_added": resources_added.scalar() or 0,
        "friends_count": friends_count.scalar() or 0,
    }


async def get_platform_analytics(db: AsyncSession) -> dict:
    total_users = await db.execute(select(func.count(User.id)))
    total_rooms = await db.execute(select(func.count(Room.id)))
    total_messages = await db.execute(select(func.count(Message.id)))
    total_resources = await db.execute(select(func.count(Resource.id)))
    active_rooms = await db.execute(
        select(func.count(Room.id)).where(Room.is_live == True)  # noqa: E712
    )

    return {
        "total_users": total_users.scalar() or 0,
        "total_rooms": total_rooms.scalar() or 0,
        "total_messages": total_messages.scalar() or 0,
        "total_resources": total_resources.scalar() or 0,
        "active_rooms": active_rooms.scalar() or 0,
    }
