"""Unique code generation utilities."""

from __future__ import annotations

import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Test


def _random_code(length: int = 6) -> str:
    """Generate a random alphanumeric code (uppercase, no ambiguous chars)."""
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def generate_test_code(session: AsyncSession, length: int = 6) -> str:
    """Generate a unique test code not already in the DB."""
    for _ in range(20):
        code = _random_code(length)
        stmt = select(Test.id).where(Test.code == code)
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return code
    raise RuntimeError("Could not generate unique test code after 20 attempts")
