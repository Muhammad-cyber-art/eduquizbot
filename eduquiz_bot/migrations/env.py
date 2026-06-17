"""Alembic migration environment — async SQLAlchemy + PostgreSQL.

Supports:
  - Offline mode: generates SQL DDL without connecting to the database
  - Online mode: connects to PostgreSQL and applies migrations directly

DATABASE_URL is read from the environment variable first (for Docker/CI),
falling back to alembic.ini's sqlalchemy.url for local development.

Usage:
  # Apply all pending migrations
  cd eduquiz_bot
  DATABASE_URL=postgresql+asyncpg://user:pass@host/db alembic upgrade head

  # Generate a new migration after changing models.py
  cd eduquiz_bot
  DATABASE_URL=postgresql+asyncpg://user:pass@host/db alembic revision --autogenerate -m "description"

  # Generate SQL without connecting (offline mode)
  cd eduquiz_bot
  alembic upgrade head --sql > schema.sql
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models so Alembic can detect schema changes during autogenerate
from app.db.base import Base
import app.db.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── URL resolution ────────────────────────────────────────────

def get_database_url() -> str:
    """Return the PostgreSQL DATABASE_URL from environment or alembic.ini."""
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set.\n"
            "Set it to your PostgreSQL connection string:\n"
            "  export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/eduquiz"
        )
    if not url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            f"DATABASE_URL must use postgresql+asyncpg:// scheme. Got: {url[:40]}...\n"
            "SQLite is not supported for migrations."
        )
    return url


# ── Offline mode ──────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Emit SQL DDL to stdout without connecting to the database."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Connect to PostgreSQL asynchronously and apply pending migrations."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        # NullPool: Alembic must not reuse connections — each migration step needs a fresh conn
        poolclass=pool.NullPool,
        connect_args={"timeout": 10.0},
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
