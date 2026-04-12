"""
FocuseMate – Room Service
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.models.room_member import RoomMember, RoomRole
from app.models.user import User


async def create_room(
    db: AsyncSession,
    owner: User,
    title: str,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    max_members: int = 50,
) -> Room:
    room = Room(
        title=title,
        description=description,
        tags=tags,
        owner_id=owner.id,
        max_members=max_members,
        meeting_link=f"https://focusmate.app/meet/{uuid.uuid4().hex[:12]}",
    )
    db.add(room)
    await db.flush()

    # Owner automatically becomes a member with OWNER role
    membership = RoomMember(
        room_id=room.id,
        user_id=owner.id,
        role=RoomRole.OWNER.value,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(room)
    return room


async def get_room_by_id(db: AsyncSession, room_id: int) -> Room | None:
    result = await db.execute(select(Room).where(Room.id == room_id))
    return result.scalar_one_or_none()


async def update_room(
    db: AsyncSession,
    room: Room,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    max_members: Optional[int] = None,
    is_live: Optional[bool] = None,
) -> Room:
    if title is not None:
        room.title = title
    if description is not None:
        room.description = description
    if tags is not None:
        room.tags = tags
    if max_members is not None:
        room.max_members = max_members
    if is_live is not None:
        room.is_live = is_live
    await db.commit()
    await db.refresh(room)
    return room


async def delete_room(db: AsyncSession, room: Room) -> None:
    await db.delete(room)
    await db.commit()


async def join_room(db: AsyncSession, room: Room, user: User) -> RoomMember:
    """Add a user to a room as a member. Raises ValueError if already joined or room is full."""
    # Check existing membership
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room.id,
            RoomMember.user_id == user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Already a member of this room")

    # Check capacity
    count_result = await db.execute(
        select(func.count(RoomMember.id)).where(RoomMember.room_id == room.id)
    )
    current_count = count_result.scalar() or 0
    if current_count >= room.max_members:
        raise ValueError("Room is full")

    membership = RoomMember(
        room_id=room.id,
        user_id=user.id,
        role=RoomRole.MEMBER.value,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def leave_room(db: AsyncSession, room_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        return False
    if membership.role == RoomRole.OWNER.value:
        raise ValueError("Owner cannot leave the room. Transfer ownership or delete the room.")
    await db.delete(membership)
    await db.commit()
    return True


async def list_user_rooms(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return rooms the user has joined, with member counts."""
    # Get rooms the user is a member of
    member_subq = (
        select(RoomMember.room_id)
        .where(RoomMember.user_id == user_id)
        .subquery()
    )
    count_subq = (
        select(
            RoomMember.room_id,
            func.count(RoomMember.id).label("member_count"),
        )
        .group_by(RoomMember.room_id)
        .subquery()
    )

    total_result = await db.execute(
        select(func.count(Room.id)).where(Room.id.in_(select(member_subq)))
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(Room, count_subq.c.member_count)
        .outerjoin(count_subq, Room.id == count_subq.c.room_id)
        .where(Room.id.in_(select(member_subq)))
        .order_by(Room.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    rooms = []
    for room, member_count in rows:
        rooms.append({
            "id": room.id,
            "title": room.title,
            "description": room.description,
            "tags": room.tags,
            "owner_id": room.owner_id,
            "is_live": room.is_live,
            "focus": room.focus,
            "max_members": room.max_members,
            "meeting_link": room.meeting_link,
            "member_count": member_count or 0,
            "created_at": room.created_at,
            "updated_at": room.updated_at,
        })
    return rooms, total


async def list_all_rooms(
    db: AsyncSession,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List all rooms with optional search and tag filter."""
    count_subq = (
        select(
            RoomMember.room_id,
            func.count(RoomMember.id).label("member_count"),
        )
        .group_by(RoomMember.room_id)
        .subquery()
    )

    query = select(Room, count_subq.c.member_count).outerjoin(
        count_subq, Room.id == count_subq.c.room_id
    )
    count_query = select(func.count(Room.id))

    if search:
        pattern = f"%{search}%"
        query = query.where(Room.title.ilike(pattern))
        count_query = count_query.where(Room.title.ilike(pattern))
    if tag:
        query = query.where(Room.tags.any(tag))
        count_query = count_query.where(Room.tags.any(tag))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Room.is_live.desc(), Room.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    rooms = []
    for room, member_count in rows:
        rooms.append({
            "id": room.id,
            "title": room.title,
            "description": room.description,
            "tags": room.tags,
            "owner_id": room.owner_id,
            "is_live": room.is_live,
            "focus": room.focus,
            "max_members": room.max_members,
            "meeting_link": room.meeting_link,
            "member_count": member_count or 0,
            "created_at": room.created_at,
            "updated_at": room.updated_at,
        })
    return rooms, total


async def get_room_members(
    db: AsyncSession,
    room_id: int,
) -> list[dict]:
    result = await db.execute(
        select(RoomMember, User)
        .join(User, RoomMember.user_id == User.id)
        .where(RoomMember.room_id == room_id)
        .order_by(RoomMember.joined_at)
    )
    rows = result.all()
    return [
        {
            "id": rm.id,
            "user_id": rm.user_id,
            "user_name": u.name,
            "user_avatar": u.avatar,
            "role": rm.role,
            "joined_at": rm.joined_at,
        }
        for rm, u in rows
    ]


async def update_member_role(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    role: str,
) -> RoomMember | None:
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        return None
    if membership.role == RoomRole.OWNER.value:
        raise ValueError("Cannot change the owner's role")
    membership.role = role
    await db.commit()
    await db.refresh(membership)
    return membership


async def remove_member(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> bool:
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        return False
    if membership.role == RoomRole.OWNER.value:
        raise ValueError("Cannot remove the room owner")
    await db.delete(membership)
    await db.commit()
    return True


async def get_user_role_in_room(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> str | None:
    result = await db.execute(
        select(RoomMember.role).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
    )
    role = result.scalar_one_or_none()
    return role


async def create_meeting_link(
    db: AsyncSession,
    user: User,
    room_id: Optional[int] = None,
    title: Optional[str] = None,
) -> dict:
    """Generate a unique meeting link, optionally tied to a room."""
    meeting_id = uuid.uuid4().hex[:12]
    meeting_link = f"https://focusmate.app/meet/{meeting_id}"

    if room_id:
        room = await get_room_by_id(db, room_id)
        if room:
            room.meeting_link = meeting_link
            await db.commit()

    return {
        "id": meeting_id,
        "meeting_link": meeting_link,
        "title": title,
    }
