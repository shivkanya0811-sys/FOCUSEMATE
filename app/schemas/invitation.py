"""
FocuseMate – Invitation schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InvitationCreate(BaseModel):
    room_id: int
    invitee_id: int


class InvitationOut(BaseModel):
    id: int
    room_id: int
    room_title: Optional[str] = None
    inviter_id: int
    inviter_name: Optional[str] = None
    invitee_id: int
    invitee_name: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationAction(BaseModel):
    action: str = Field(..., pattern="^(accept|reject)$")


class InvitationListOut(BaseModel):
    invitations: list[InvitationOut]
    total: int
