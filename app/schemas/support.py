"""
FocuseMate – Support ticket schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SupportTicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    category: str = Field(default="general", pattern="^(bug|feature|account|general)$")


class SupportTicketOut(BaseModel):
    id: int
    user_id: int
    subject: str
    description: str
    category: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportTicketListOut(BaseModel):
    tickets: list[SupportTicketOut]
    total: int


class SupportTicketStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|in_progress|resolved|closed)$")
