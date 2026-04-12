"""
FocuseMate – RoomInvitation model
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InvitationStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RoomInvitation(Base):
    __tablename__ = "room_invitations"
    __table_args__ = (
        UniqueConstraint("room_id", "invitee_id", name="uq_room_invitation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inviter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invitee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(InvitationStatus, name="invitation_status_enum", create_constraint=True, values_callable=lambda e: [i.value for i in e]),
        default=InvitationStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── relationships ────────────────────────────────────────────
    room = relationship("Room", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id], lazy="selectin")
    invitee = relationship("User", foreign_keys=[invitee_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<RoomInvitation room={self.room_id} invitee={self.invitee_id} status={self.status}>"
