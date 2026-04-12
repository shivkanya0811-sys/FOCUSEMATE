"""
FocuseMate Backend - Async Database Session
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _import_all_models() -> None:
    """Import every model so that Base.metadata is fully populated."""
    import app.models.user  # noqa: F401
    import app.models.room  # noqa: F401
    import app.models.room_member  # noqa: F401
    import app.models.friend_request  # noqa: F401
    import app.models.message  # noqa: F401
    import app.models.resource  # noqa: F401
    import app.models.room_invitation  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.support_ticket  # noqa: F401
    import app.models.user_settings  # noqa: F401


async def init_db() -> None:
    """Create all tables (use Alembic migrations in production)."""
    _import_all_models()
    from app.db.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the engine connection pool."""
    await engine.dispose()
