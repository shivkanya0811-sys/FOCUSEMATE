"""
FocuseMate – User Service
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession,
    user: User,
    name: Optional[str] = None,
    bio: Optional[str] = None,
    avatar: Optional[str] = None,
) -> User:
    if name is not None:
        user.name = name
    if bio is not None:
        user.bio = bio
    if avatar is not None:
        user.avatar = avatar
    await db.commit()
    await db.refresh(user)
    return user


async def search_users(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[User], int]:
    """Search users by name or email (case-insensitive partial match)."""
    pattern = f"%{query}%"
    where_clause = or_(
        User.name.ilike(pattern),
        User.email.ilike(pattern),
    )
    count_result = await db.execute(select(func.count(User.id)).where(where_clause))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(User)
        .where(where_clause)
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.name)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total
