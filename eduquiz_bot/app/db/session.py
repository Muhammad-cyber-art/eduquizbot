"""PostgreSQL database session factory — asyncpg + SQLAlchemy 2.

No SQLite. No create_all. Schema is managed exclusively by Alembic.

Pool sizing (conservative for standard VPS, ~2GB RAM):
  pool_size=5     : 5 persistent idle connections
  max_overflow=10 : up to 10 extra connections on burst (total 15)
  pool_timeout=30 : wait max 30s for a connection before raising PoolTimeout
  pool_recycle=1800: recycle connections every 30 min (prevents stale conn errors)
  pool_pre_ping=True: SELECT 1 before using a connection (detects dropped connections)
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# server_settings: override PostgreSQL connection parameters at the session level
# prepared_statement_cache_size=0: disable asyncpg's PS cache (avoids issues with PgBouncer)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # Connection pool
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    # asyncpg-specific: disable statement cache for PgBouncer compatibility
    # and set application_name for pg_stat_activity visibility
    connect_args={
        "server_settings": {
            "application_name": "eduquiz_bot",
            "timezone": "UTC",
        },
        "prepared_statement_cache_size": 0,
    },
)

# ── Session factory ───────────────────────────────────────────────────────────
# expire_on_commit=False: prevent lazy-load errors after commit in async contexts
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Database startup ──────────────────────────────────────────────────────────

async def init_db() -> None:
    """Verify database connectivity at startup.

    Schema management is handled exclusively by Alembic (run via entrypoint.sh).
    This function only confirms the connection is live — it does NOT create tables.
    """
    from sqlalchemy import text
    import asyncio

    async def _ping():
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        await asyncio.wait_for(_ping(), timeout=10.0)
    except asyncio.TimeoutError:
        raise RuntimeError("Database connection timed out after 10 seconds.")


# ── FastAPI / aiogram dependency ──────────────────────────────────────────────

async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Async generator yielding a database session per request.

    Automatically rolls back on unhandled exceptions and closes on exit.

    Usage (FastAPI):
        session: AsyncSession = Depends(get_async_session)
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Alias used throughout the codebase as a FastAPI dependency
get_async_session = get_session
