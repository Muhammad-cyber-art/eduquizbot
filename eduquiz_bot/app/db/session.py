from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import event

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    **({} if _is_sqlite else {"pool_size": 10, "max_overflow": 20}),
)

# Optimize SQLite performance for concurrent writes/reads
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables (for SQLite dev mode). No-op if tables already exist."""
    from app.db.base import Base
    import app.db.models  # noqa: F401 — ensure models are imported
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Check and add new columns if they do not exist (SQLite migration helper)
        def migrate(sync_conn):
            from sqlalchemy import text
            # Check tests columns
            res = sync_conn.execute(text("PRAGMA table_info(tests);"))
            columns = [row[1] for row in res.fetchall()]
            if "test_type" not in columns:
                sync_conn.execute(text("ALTER TABLE tests ADD COLUMN test_type VARCHAR(16) DEFAULT 'standard' NOT NULL;"))
                
            # Check answers columns
            res = sync_conn.execute(text("PRAGMA table_info(answers);"))
            columns = [row[1] for row in res.fetchall()]
            if "selected_text" not in columns:
                sync_conn.execute(text("ALTER TABLE answers ADD COLUMN selected_text TEXT;"))
                
        await conn.run_sync(migrate)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI-style dependency; also usable directly in handlers."""
    async with async_session() as session:
        yield session


# Alias for FastAPI dependency injection
get_async_session = get_session
