"""Deadline timer service — auto-expires attempts when time runs out."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Attempt
from app.db.session import async_session
from app.services.attempts import finish_attempt

logger = logging.getLogger(__name__)


async def check_expired_attempts() -> None:
    """Periodic task: find in-progress attempts past their deadline and auto-finish them."""
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        stmt = select(Attempt).where(
            Attempt.status == "in_progress",
            Attempt.deadline_at.isnot(None),
            Attempt.deadline_at <= now,
        ).options(selectinload(Attempt.answers))
        result = await session.execute(stmt)
        expired = result.scalars().all()
        for att in expired:
            try:
                await finish_attempt(session, att.id, expired=True)
                logger.info("Auto-expired attempt %s", att.id)
            except Exception:
                logger.exception("Failed to expire attempt %s", att.id)


async def run_timer_loop(interval: int = 30) -> None:
    """Background loop that checks for expired attempts every `interval` seconds."""
    while True:
        try:
            await check_expired_attempts()
        except Exception:
            logger.exception("Timer check failed")
        await asyncio.sleep(interval)
