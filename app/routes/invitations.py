"""
FocuseMate – Invitation Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.invitation import (
    InvitationAction,
    InvitationCreate,
    InvitationListOut,
    InvitationOut,
)
from app.services.invitation_service import (
    create_invitation,
    get_user_invitations,
    respond_to_invitation,
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("/", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
async def send_invitation(
    body: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a user to a room."""
    try:
        inv = await create_invitation(db, body.room_id, current_user.id, body.invitee_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Notify the invitee
    await create_notification(
        db,
        user_id=body.invitee_id,
        notification_type="room_invite",
        title="Room Invitation",
        body=f"{current_user.name} invited you to join '{inv['room_title']}'.",
        actor_id=current_user.id,
        reference_id=inv["id"],
    )

    return InvitationOut(**inv)


@router.put("/{invitation_id}", response_model=InvitationOut)
async def respond_invite(
    invitation_id: int,
    body: InvitationAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or reject a room invitation."""
    try:
        inv = await respond_to_invitation(db, invitation_id, current_user.id, body.action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return InvitationOut(**inv)


@router.get("/", response_model=InvitationListOut)
async def list_invitations(
    status_filter: str | None = Query(None, description="Filter by status (pending, accepted, rejected)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get invitations received by the current user."""
    invitations, total = await get_user_invitations(
        db, current_user.id, status_filter=status_filter
    )
    return InvitationListOut(
        invitations=[InvitationOut(**i) for i in invitations],
        total=total,
    )
