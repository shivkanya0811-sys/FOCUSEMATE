"""
FocuseMate – Helper utilities
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def generate_meeting_id() -> str:
    """Generate a short meeting ID like abc-defg-hij."""
    raw = uuid.uuid4().hex[:10]
    return f"{raw[:3]}-{raw[3:7]}-{raw[7:]}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
