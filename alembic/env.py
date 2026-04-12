"""
Alembic environment configuration for FocuseMate.
Uses async engine from the application's database module.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Load app config ─────────────────────────────────────────────
from app.core.config import settings
from app.db.base import Base

# ── Import all models so Base.metadata is populated ──────────────
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

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the app's DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL generation only)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
