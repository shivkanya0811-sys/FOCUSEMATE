"""
FocuseMate – Resource schemas (room-scoped)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    resource_type: str = Field(default="link", pattern="^(video|pdf|link|note|pyq)$")
    link: Optional[str] = Field(None, max_length=1024)


class ResourceOut(BaseModel):
    id: int
    room_id: int
    added_by: Optional[int] = None
    added_by_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    resource_type: str
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceListOut(BaseModel):
    resources: list[ResourceOut]
    total: int
