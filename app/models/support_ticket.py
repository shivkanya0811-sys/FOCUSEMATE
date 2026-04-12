"""
FocuseMate – SupportTicket model
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


class TicketStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketCategory(str, PyEnum):
    BUG = "bug"
    FEATURE = "feature"
    ACCOUNT = "account"
    GENERAL = "general"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(TicketCategory, name="ticket_category_enum", create_constraint=True, values_callable=lambda e: [i.value for i in e]),
        default=TicketCategory.GENERAL.value,
    )
    status: Mapped[str] = mapped_column(
        Enum(TicketStatus, name="ticket_status_enum", create_constraint=True, values_callable=lambda e: [i.value for i in e]),
        default=TicketStatus.OPEN.value,
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
    user = relationship("User", back_populates="support_tickets", lazy="selectin")

    def __repr__(self) -> str:
        return f"<SupportTicket id={self.id} user={self.user_id} status={self.status}>"
