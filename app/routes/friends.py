"""
FocuseMate – Friend Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.friend import (
    FriendListOut,
    FriendOut,
    FriendRequestAction,
    FriendRequestCreate,
    FriendRequestOut,
)
from app.services.friend_service import (
    get_pending_requests,
    get_sent_requests,
    list_friends,
    respond_to_friend_request,
    send_friend_request,
    unfriend,
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.post("/request", response_model=FriendRequestOut, status_code=status.HTTP_201_CREATED)
async def send_request(
    body: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a friend request."""
    try:
        fr = await send_friend_request(db, current_user.id, body.receiver_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Create notification for receiver
    await create_notification(
        db,
        user_id=body.receiver_id,
        notification_type="friend_request",
        title="New Friend Request",
        body=f"{current_user.name} sent you a friend request.",
        actor_id=current_user.id,
        reference_id=fr.id,
    )

    return FriendRequestOut(
        id=fr.id,
        sender_id=fr.sender_id,
        sender_name=current_user.name,
        sender_avatar=current_user.avatar,
        receiver_id=fr.receiver_id,
        receiver_name="",
        receiver_avatar=None,
        status=fr.status,
        created_at=fr.created_at,
    )


@router.put("/request/{request_id}", response_model=FriendRequestOut)
async def respond_request(
    request_id: int,
    body: FriendRequestAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or reject a friend request."""
    try:
        fr = await respond_to_friend_request(db, request_id, current_user.id, body.action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Notify sender if accepted
    if body.action == "accept":
        await create_notification(
            db,
            user_id=fr.sender_id,
            notification_type="friend_accepted",
            title="Friend Request Accepted",
            body=f"{current_user.name} accepted your friend request.",
            actor_id=current_user.id,
            reference_id=fr.id,
        )

    return FriendRequestOut(
        id=fr.id,
        sender_id=fr.sender_id,
        sender_name=fr.sender.name if fr.sender else "",
        sender_avatar=fr.sender.avatar if fr.sender else None,
        receiver_id=fr.receiver_id,
        receiver_name=fr.receiver.name if fr.receiver else "",
        receiver_avatar=fr.receiver.avatar if fr.receiver else None,
        status=fr.status,
        created_at=fr.created_at,
    )


@router.get("/", response_model=FriendListOut)
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all accepted friends."""
    friends = await list_friends(db, current_user.id)
    return FriendListOut(
        friends=[FriendOut.model_validate(f) for f in friends],
        total=len(friends),
    )


@router.get("/requests/pending", response_model=list[FriendRequestOut])
async def get_pending(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending friend requests received by the current user."""
    requests = await get_pending_requests(db, current_user.id)
    return [FriendRequestOut(**r) for r in requests]


@router.get("/requests/sent", response_model=list[FriendRequestOut])
async def get_sent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending friend requests sent by the current user."""
    requests = await get_sent_requests(db, current_user.id)
    return [FriendRequestOut(**r) for r in requests]


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a friend."""
    removed = await unfriend(db, current_user.id, friend_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")
