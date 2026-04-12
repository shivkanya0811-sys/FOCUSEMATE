"""
FocuseMate – Message model
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MessageType(str, PyEnum):
    TEXT = "text"
    LINK = "link"
    CODE = "code"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        Enum(MessageType, name="message_type_enum", create_constraint=True, values_callable=lambda e: [i.value for i in e]),
        default=MessageType.TEXT.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    # ── relationships ────────────────────────────────────────────
    room = relationship("Room", back_populates="messages")
    sender = relationship("User", back_populates="messages", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Message id={self.id} room={self.room_id} sender={self.sender_id}>"
