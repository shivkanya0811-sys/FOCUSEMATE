"""
FocuseMate – Friend Service
"""
from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friend_request import FriendRequest, FriendStatus
from app.models.user import User


async def send_friend_request(
    db: AsyncSession,
    sender_id: int,
    receiver_id: int,
) -> FriendRequest:
    if sender_id == receiver_id:
        raise ValueError("Cannot send a friend request to yourself")

    # Check if already friends or pending
    result = await db.execute(
        select(FriendRequest).where(
            or_(
                and_(
                    FriendRequest.sender_id == sender_id,
                    FriendRequest.receiver_id == receiver_id,
                ),
                and_(
                    FriendRequest.sender_id == receiver_id,
                    FriendRequest.receiver_id == sender_id,
                ),
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status == FriendStatus.ACCEPTED.value:
            raise ValueError("Already friends")
        if existing.status == FriendStatus.PENDING.value:
            raise ValueError("Friend request already pending")
        if existing.status == FriendStatus.REJECTED.value:
            # Allow re-sending after rejection
            existing.status = FriendStatus.PENDING.value
            existing.sender_id = sender_id
            existing.receiver_id = receiver_id
            await db.commit()
            await db.refresh(existing)
            return existing

    # Verify receiver exists
    recv_result = await db.execute(select(User).where(User.id == receiver_id))
    if not recv_result.scalar_one_or_none():
        raise ValueError("User not found")

    fr = FriendRequest(
        sender_id=sender_id,
        receiver_id=receiver_id,
        status=FriendStatus.PENDING.value,
    )
    db.add(fr)
    await db.commit()
    await db.refresh(fr)
    return fr


async def respond_to_friend_request(
    db: AsyncSession,
    request_id: int,
    user_id: int,
    action: str,
) -> FriendRequest:
    result = await db.execute(
        select(FriendRequest).where(FriendRequest.id == request_id)
    )
    fr = result.scalar_one_or_none()
    if not fr:
        raise ValueError("Friend request not found")
    if fr.receiver_id != user_id:
        raise ValueError("Not authorized to respond to this request")
    if fr.status != FriendStatus.PENDING.value:
        raise ValueError("Request already processed")

    fr.status = FriendStatus.ACCEPTED.value if action == "accept" else FriendStatus.REJECTED.value
    await db.commit()
    await db.refresh(fr)
    return fr


async def list_friends(
    db: AsyncSession,
    user_id: int,
) -> list[User]:
    """Return all accepted friends for a user."""
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.status == FriendStatus.ACCEPTED.value,
            or_(
                FriendRequest.sender_id == user_id,
                FriendRequest.receiver_id == user_id,
            ),
        )
    )
    requests = result.scalars().all()

    friend_ids = set()
    for fr in requests:
        if fr.sender_id == user_id:
            friend_ids.add(fr.receiver_id)
        else:
            friend_ids.add(fr.sender_id)

    if not friend_ids:
        return []

    result = await db.execute(
        select(User).where(User.id.in_(friend_ids)).order_by(User.name)
    )
    return result.scalars().all()


async def get_pending_requests(
    db: AsyncSession,
    user_id: int,
) -> list[dict]:
    """Get pending friend requests received by the user."""
    result = await db.execute(
        select(FriendRequest, User)
        .join(User, FriendRequest.sender_id == User.id)
        .where(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == FriendStatus.PENDING.value,
        )
        .order_by(FriendRequest.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": fr.id,
            "sender_id": fr.sender_id,
            "sender_name": u.name,
            "sender_avatar": u.avatar,
            "receiver_id": fr.receiver_id,
            "receiver_name": "",
            "receiver_avatar": None,
            "status": fr.status,
            "created_at": fr.created_at,
        }
        for fr, u in rows
    ]


async def get_sent_requests(
    db: AsyncSession,
    user_id: int,
) -> list[dict]:
    """Get pending friend requests sent by the user."""
    result = await db.execute(
        select(FriendRequest, User)
        .join(User, FriendRequest.receiver_id == User.id)
        .where(
            FriendRequest.sender_id == user_id,
            FriendRequest.status == FriendStatus.PENDING.value,
        )
        .order_by(FriendRequest.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": fr.id,
            "sender_id": fr.sender_id,
            "sender_name": "",
            "sender_avatar": None,
            "receiver_id": fr.receiver_id,
            "receiver_name": u.name,
            "receiver_avatar": u.avatar,
            "status": fr.status,
            "created_at": fr.created_at,
        }
        for fr, u in rows
    ]


async def unfriend(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> bool:
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.status == FriendStatus.ACCEPTED.value,
            or_(
                and_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.receiver_id == friend_id,
                ),
                and_(
                    FriendRequest.sender_id == friend_id,
                    FriendRequest.receiver_id == user_id,
                ),
            ),
        )
    )
    fr = result.scalar_one_or_none()
    if not fr:
        return False
    await db.delete(fr)
    await db.commit()
    return True
