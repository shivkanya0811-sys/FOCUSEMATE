"""
FocuseMate – UserSettings model
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    # ── Notification preferences ─────────────────────────────────
    notify_friend_requests: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_room_invites: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_messages: Mapped[bool] = mapped_column(Boolean, default=True)
    study_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    motivational_quotes: Mapped[bool] = mapped_column(Boolean, default=True)
    # ── Privacy ──────────────────────────────────────────────────
    profile_visibility: Mapped[str] = mapped_column(String(20), default="public")
    show_online_status: Mapped[bool] = mapped_column(Boolean, default=True)
    # ── UI ───────────────────────────────────────────────────────
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    # ── Timestamps ───────────────────────────────────────────────
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── relationships ────────────────────────────────────────────
    user = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id}>"
