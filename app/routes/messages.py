"""
FocuseMate – Message Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListOut, MessageOut
from app.services.message_service import create_message, get_room_messages
from app.services.room_service import get_user_role_in_room

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a room (REST fallback — prefer WebSocket)."""
    # Verify user is a member
    role = await get_user_role_in_room(db, body.room_id, current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this room",
        )
    msg = await create_message(
        db,
        room_id=body.room_id,
        sender_id=current_user.id,
        content=body.content,
        message_type=body.message_type,
    )
    return MessageOut(**msg)


@router.get("/{room_id}", response_model=MessageListOut)
async def get_messages(
    room_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_id: int | None = Query(None, description="Fetch messages before this ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch paginated messages for a room."""
    role = await get_user_role_in_room(db, room_id, current_user.id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this room",
        )
    messages, total, has_more = await get_room_messages(
        db, room_id, limit=limit, offset=offset, before_id=before_id
    )
    return MessageListOut(
        messages=[MessageOut(**m) for m in messages],
        total=total,
        has_more=has_more,
    )
