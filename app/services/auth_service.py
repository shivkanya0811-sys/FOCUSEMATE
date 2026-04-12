"""
FocuseMate – Auth Service
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.user_settings import UserSettings


async def register_user(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
) -> User:
    """Create a new user and initialize default settings."""
    # Check for existing email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ValueError("Email already in use")

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        avatar=f"https://api.dicebear.com/7.x/avataaars/png?seed={email}",
    )
    db.add(user)
    await db.flush()

    # Create default settings
    settings = UserSettings(user_id=user.id)
    db.add(settings)

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Validate credentials and return user or None."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def generate_tokens(user: User) -> dict:
    """Generate access and refresh tokens for a given user."""
    data = {"sub": str(user.id)}
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer",
        "user_data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": user.avatar,
            "level": user.level,
            "xp": user.xp,
        },
    }


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> dict | None:
    """Validate a refresh token and issue a new access token pair."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    return generate_tokens(user)
