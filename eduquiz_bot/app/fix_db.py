"""Quick fix script: drop all tables, recreate with correct schema, then seed."""
import asyncio
import os

async def setup():
    from app.db.session import init_db, engine, async_session
    from app.db.base import Base
    from app.db.models import TeacherInviteCode
    import app.db.models  # ensure all models loaded
    from sqlalchemy import select, func

    # Drop all tables and recreate
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropped all tables.")
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables with new schema.")

    # Seed
    async with async_session() as session:
        defaults = [
            TeacherInviteCode(code="1234", is_active=True),
            TeacherInviteCode(code="TEACHER2024", is_active=True),
        ]
        session.add_all(defaults)
        await session.commit()
        count = (await session.execute(
            select(func.count()).select_from(TeacherInviteCode)
        )).scalar_one()
        print(f"Seeded {count} invite codes: '1234' and 'TEACHER2024'")

    await engine.dispose()
    print("Done! Start the bot with: python -m app.main")

if __name__ == "__main__":
    asyncio.run(setup())
