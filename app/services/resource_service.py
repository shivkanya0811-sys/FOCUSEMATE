"""
FocuseMate – Resource Service (room-scoped)
"""
from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource, ResourceType
from app.models.room_member import RoomMember
from app.models.user import User


YOUTUBE_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|shorts/)|youtu\.be/)[\w\-]{11}"
)


def is_valid_youtube_link(url: str) -> bool:
    return bool(YOUTUBE_REGEX.match(url))


async def add_resource(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    resource_type: str = "link",
    link: Optional[str] = None,
) -> dict:
    # Validate YouTube links
    if resource_type == "video" and link and not is_valid_youtube_link(link):
        # Allow non-YouTube video links too, but warn if it looks like a YouTube attempt
        pass  # Be lenient – accept any URL

    resource = Resource(
        room_id=room_id,
        added_by=user_id,
        title=title,
        description=description,
        resource_type=resource_type,
        link=link,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    return {
        "id": resource.id,
        "room_id": resource.room_id,
        "added_by": resource.added_by,
        "added_by_name": user.name if user else None,
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type,
        "link": resource.link,
        "created_at": resource.created_at,
    }


async def get_room_resources(
    db: AsyncSession,
    room_id: int,
    resource_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    count_query = select(func.count(Resource.id)).where(Resource.room_id == room_id)
    query = (
        select(Resource, User)
        .outerjoin(User, Resource.added_by == User.id)
        .where(Resource.room_id == room_id)
    )

    if resource_type:
        count_query = count_query.where(Resource.resource_type == resource_type)
        query = query.where(Resource.resource_type == resource_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Resource.created_at.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    resources = [
        {
            "id": r.id,
            "room_id": r.room_id,
            "added_by": r.added_by,
            "added_by_name": u.name if u else None,
            "title": r.title,
            "description": r.description,
            "resource_type": r.resource_type,
            "link": r.link,
            "created_at": r.created_at,
        }
        for r, u in rows
    ]
    return resources, total


async def delete_resource(
    db: AsyncSession,
    resource_id: int,
    user_id: int,
    room_id: int,
) -> bool:
    """Delete a resource. Only owner/admin of the room or the resource creator can delete."""
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.room_id == room_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        return False

    # Check if user is the resource creator
    if resource.added_by == user_id:
        await db.delete(resource)
        await db.commit()
        return True

    # Check if user is owner/admin of the room
    member_result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
    )
    membership = member_result.scalar_one_or_none()
    if membership and membership.role in ("owner", "admin"):
        await db.delete(resource)
        await db.commit()
        return True

    return False
