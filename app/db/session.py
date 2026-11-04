"""Async engine & session factory — supports SQLite (dev) and PostgreSQL (prod)."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    **({} if _is_sqlite else {"pool_size": 10, "max_overflow": 20}),
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables (for SQLite dev mode). No-op if tables already exist."""
    from app.db.base import Base
    import app.db.models  # noqa: F401 — ensure models are imported
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI-style dependency; also usable directly in handlers."""
    async with async_session() as session:
        yield session


# Alias for FastAPI dependency injection
get_async_session = get_session
