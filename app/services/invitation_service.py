"""
FocuseMate – Invitation Service
"""
from __future__ import annotations

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.models.room_invitation import InvitationStatus, RoomInvitation
from app.models.room_member import RoomMember, RoomRole
from app.models.user import User


async def create_invitation(
    db: AsyncSession,
    room_id: int,
    inviter_id: int,
    invitee_id: int,
) -> dict:
    if inviter_id == invitee_id:
        raise ValueError("Cannot invite yourself")

    # Verify room exists
    room_result = await db.execute(select(Room).where(Room.id == room_id))
    room = room_result.scalar_one_or_none()
    if not room:
        raise ValueError("Room not found")

    # Verify inviter is a member
    member_result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == inviter_id,
        )
    )
    if not member_result.scalar_one_or_none():
        raise ValueError("Only room members can send invitations")

    # Verify invitee exists
    invitee_result = await db.execute(select(User).where(User.id == invitee_id))
    invitee = invitee_result.scalar_one_or_none()
    if not invitee:
        raise ValueError("Invitee not found")

    # Check if invitee is already a member
    existing_member = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == invitee_id,
        )
    )
    if existing_member.scalar_one_or_none():
        raise ValueError("User is already a member of this room")

    # Check for existing pending invitation
    existing_inv = await db.execute(
        select(RoomInvitation).where(
            RoomInvitation.room_id == room_id,
            RoomInvitation.invitee_id == invitee_id,
            RoomInvitation.status == InvitationStatus.PENDING.value,
        )
    )
    if existing_inv.scalar_one_or_none():
        raise ValueError("Invitation already pending")

    invitation = RoomInvitation(
        room_id=room_id,
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        status=InvitationStatus.PENDING.value,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    inviter_result = await db.execute(select(User).where(User.id == inviter_id))
    inviter = inviter_result.scalar_one_or_none()

    return {
        "id": invitation.id,
        "room_id": invitation.room_id,
        "room_title": room.title,
        "inviter_id": invitation.inviter_id,
        "inviter_name": inviter.name if inviter else None,
        "invitee_id": invitation.invitee_id,
        "invitee_name": invitee.name if invitee else None,
        "status": invitation.status,
        "created_at": invitation.created_at,
    }


async def respond_to_invitation(
    db: AsyncSession,
    invitation_id: int,
    user_id: int,
    action: str,
) -> dict:
    result = await db.execute(
        select(RoomInvitation).where(RoomInvitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise ValueError("Invitation not found")
    if invitation.invitee_id != user_id:
        raise ValueError("Not authorized to respond to this invitation")
    if invitation.status != InvitationStatus.PENDING.value:
        raise ValueError("Invitation already processed")

    if action == "accept":
        invitation.status = InvitationStatus.ACCEPTED.value
        # Add user to room
        membership = RoomMember(
            room_id=invitation.room_id,
            user_id=user_id,
            role=RoomRole.MEMBER.value,
        )
        db.add(membership)
    else:
        invitation.status = InvitationStatus.REJECTED.value

    await db.commit()
    await db.refresh(invitation)

    room_result = await db.execute(select(Room).where(Room.id == invitation.room_id))
    room = room_result.scalar_one_or_none()

    return {
        "id": invitation.id,
        "room_id": invitation.room_id,
        "room_title": room.title if room else None,
        "inviter_id": invitation.inviter_id,
        "invitee_id": invitation.invitee_id,
        "status": invitation.status,
        "created_at": invitation.created_at,
    }


async def get_user_invitations(
    db: AsyncSession,
    user_id: int,
    status_filter: str | None = None,
) -> tuple[list[dict], int]:
    """Get invitations received by the user."""
    query = (
        select(RoomInvitation, Room, User)
        .join(Room, RoomInvitation.room_id == Room.id)
        .join(User, RoomInvitation.inviter_id == User.id)
        .where(RoomInvitation.invitee_id == user_id)
    )
    count_query = select(func.count(RoomInvitation.id)).where(
        RoomInvitation.invitee_id == user_id
    )

    if status_filter:
        query = query.where(RoomInvitation.status == status_filter)
        count_query = count_query.where(RoomInvitation.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.order_by(RoomInvitation.created_at.desc()))
    rows = result.all()

    invitations = [
        {
            "id": inv.id,
            "room_id": inv.room_id,
            "room_title": room.title,
            "inviter_id": inv.inviter_id,
            "inviter_name": inviter.name,
            "invitee_id": inv.invitee_id,
            "invitee_name": None,
            "status": inv.status,
            "created_at": inv.created_at,
        }
        for inv, room, inviter in rows
    ]
    return invitations, total
