"""
FocuseMate – Room Members Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.room import RoomMemberOut, RoomMemberUpdate
from app.services.room_service import (
    get_room_by_id,
    get_room_members,
    get_user_role_in_room,
    remove_member,
    update_member_role,
)

router = APIRouter(prefix="/rooms/{room_id}/members", tags=["Room Members"])


@router.get("/", response_model=list[RoomMemberOut])
async def list_members(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members of a room."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # Verify the requester is a member
    role = await get_user_role_in_room(db, room_id, current_user.id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this room")

    members = await get_room_members(db, room_id)
    return [RoomMemberOut(**m) for m in members]


@router.patch("/{user_id}", response_model=RoomMemberOut)
async def update_role(
    room_id: int,
    user_id: int,
    body: RoomMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a member's role (owner only)."""
    role = await get_user_role_in_room(db, room_id, current_user.id)
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room owner can change roles",
        )
    try:
        membership = await update_member_role(db, room_id, user_id, body.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Re-fetch for full data
    members = await get_room_members(db, room_id)
    for m in members:
        if m["user_id"] == user_id:
            return RoomMemberOut(**m)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def kick_member(
    room_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from a room (owner/admin only)."""
    role = await get_user_role_in_room(db, room_id, current_user.id)
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    try:
        removed = await remove_member(db, room_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
