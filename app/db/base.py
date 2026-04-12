"""
FocuseMate Backend - SQLAlchemy Declarative Base

Models import this Base to define tables.
The model registry happens via a separate function called during startup.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
