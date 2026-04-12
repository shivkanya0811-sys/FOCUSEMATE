"""
FocuseMate – Validators
"""
from __future__ import annotations

import re


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}",
        r"^(https?://)?(www\.)?youtu\.be/[\w-]{11}",
        r"^(https?://)?(www\.)?youtube\.com/embed/[\w-]{11}",
        r"^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}",
    ]
    return any(re.match(p, url) for p in patterns)


def is_valid_url(url: str) -> bool:
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and truncate."""
    return value.strip()[:max_length]
