"""
FocuseMate – Room model
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    focus: Mapped[int] = mapped_column(Integer, default=0)
    max_members: Mapped[int] = mapped_column(Integer, default=50)
    meeting_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── relationships ────────────────────────────────────────────
    owner = relationship("User", back_populates="owned_rooms", lazy="selectin")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan", lazy="selectin")
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan", lazy="selectin")
    resources = relationship("Resource", back_populates="room", cascade="all, delete-orphan", lazy="selectin")
    invitations = relationship("RoomInvitation", back_populates="room", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Room id={self.id} title={self.title}>"
