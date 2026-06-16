"""Database seed script — inserts a default teacher PIN for testing.

Usage:
    cd eduquiz_bot
    python -m app.seed
"""

import asyncio

from app.db.session import async_session, init_db
from app.db.models import TeacherInviteCode


async def seed() -> None:
    """Insert default invite codes if none exist."""
    await init_db()

    async with async_session() as session:
        from sqlalchemy import select, func
        count = (await session.execute(
            select(func.count()).select_from(TeacherInviteCode)
        )).scalar_one()

        if count == 0:
            # Default PINs for testing
            defaults = [
                TeacherInviteCode(code="1234", is_active=True),
                TeacherInviteCode(code="TEACHER2024", is_active=True),
            ]
            session.add_all(defaults)
            await session.commit()
            print("Seeded 2 default PINs: '1234' and 'TEACHER2024'")
        else:
            print(f"{count} invite code(s) already exist. Skipping seed.")


if __name__ == "__main__":
    asyncio.run(seed())
