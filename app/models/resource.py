"""
FocuseMate – Resource model (room-scoped)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResourceType(str, PyEnum):
    VIDEO = "video"
    PDF = "pdf"
    LINK = "link"
    NOTE = "note"
    PYQ = "pyq"


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(
        Enum(ResourceType, name="resource_type_enum", create_constraint=True, values_callable=lambda e: [i.value for i in e]),
        default=ResourceType.LINK.value,
    )
    link: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── relationships ────────────────────────────────────────────
    room = relationship("Room", back_populates="resources")
    added_by_user = relationship("User", back_populates="resources", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Resource id={self.id} title={self.title} room={self.room_id}>"
