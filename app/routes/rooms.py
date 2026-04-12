"""
FocuseMate – Room Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.room import (
    MeetingCreate,
    MeetingOut,
    RoomCreate,
    RoomListOut,
    RoomOut,
    RoomUpdate,
)
from app.services.room_service import (
    create_meeting_link,
    create_room,
    delete_room,
    get_room_by_id,
    get_user_role_in_room,
    join_room,
    leave_room,
    list_all_rooms,
    list_user_rooms,
    update_room,
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_new_room(
    body: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new virtual room."""
    room = await create_room(
        db,
        owner=current_user,
        title=body.title,
        description=body.description,
        tags=body.tags,
        max_members=body.max_members,
    )
    return RoomOut(
        id=room.id,
        title=room.title,
        description=room.description,
        tags=room.tags,
        owner_id=room.owner_id,
        is_live=room.is_live,
        focus=room.focus,
        max_members=room.max_members,
        meeting_link=room.meeting_link,
        member_count=1,
        created_at=room.created_at,
        updated_at=room.updated_at,
    )


@router.get("/", response_model=RoomListOut)
async def get_all_rooms(
    search: str | None = Query(None, description="Search rooms by title"),
    tag: str | None = Query(None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all rooms with optional search and tag filter."""
    rooms, total = await list_all_rooms(db, search=search, tag=tag, limit=limit, offset=offset)
    return RoomListOut(
        rooms=[RoomOut(**r) for r in rooms],
        total=total,
    )


@router.get("/my", response_model=RoomListOut)
async def get_my_rooms(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List rooms the current user has joined."""
    rooms, total = await list_user_rooms(db, current_user.id, limit, offset)
    return RoomListOut(
        rooms=[RoomOut(**r) for r in rooms],
        total=total,
    )


@router.get("/{room_id}", response_model=RoomOut)
async def get_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get room details."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    member_count = len(room.members) if room.members else 0
    return RoomOut(
        id=room.id,
        title=room.title,
        description=room.description,
        tags=room.tags,
        owner_id=room.owner_id,
        is_live=room.is_live,
        focus=room.focus,
        max_members=room.max_members,
        meeting_link=room.meeting_link,
        member_count=member_count,
        created_at=room.created_at,
        updated_at=room.updated_at,
    )


@router.patch("/{room_id}", response_model=RoomOut)
async def update_existing_room(
    room_id: int,
    body: RoomUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a room (owner/admin only)."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    role = await get_user_role_in_room(db, room_id, current_user.id)
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    updated = await update_room(
        db, room,
        title=body.title,
        description=body.description,
        tags=body.tags,
        max_members=body.max_members,
        is_live=body.is_live,
    )
    member_count = len(updated.members) if updated.members else 0
    return RoomOut(
        id=updated.id,
        title=updated.title,
        description=updated.description,
        tags=updated.tags,
        owner_id=updated.owner_id,
        is_live=updated.is_live,
        focus=updated.focus,
        max_members=updated.max_members,
        meeting_link=updated.meeting_link,
        member_count=member_count,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a room (owner only)."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete a room")
    await delete_room(db, room)


@router.post("/{room_id}/join", status_code=status.HTTP_200_OK)
async def join_existing_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a room."""
    room = await get_room_by_id(db, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    try:
        membership = await join_room(db, room, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "Joined room successfully", "role": membership.role}


@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_existing_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a room."""
    try:
        left = await leave_room(db, room_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not left:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a member of this room")
    return {"message": "Left room successfully"}


# ── Meeting link generation ──────────────────────────────────────
@router.post("/meetings/create", response_model=MeetingOut)
async def create_meeting(
    body: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a unique meeting link."""
    result = await create_meeting_link(
        db, current_user, room_id=body.room_id, title=body.title
    )
    return MeetingOut(**result)
