"""Authentication & user management service.

All blocking CPU-bound operations (bcrypt) are run in a thread pool
via asyncio.to_thread() to avoid blocking the async event loop.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from functools import partial

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessRequest, TeacherInviteCode, User, UserRole

# ── Password hashing (bcrypt) ─────────────────────────────────
# bcrypt is intentionally slow (~100ms per call).
# ALL bcrypt calls MUST be run in asyncio.to_thread() to avoid
# blocking the event loop and stalling the entire bot.


def _hash_password_sync(password: str) -> str:
    """Blocking bcrypt hash — must be called via asyncio.to_thread()."""
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def _verify_password_sync(plain: str, hashed: str) -> bool:
    """Blocking bcrypt verify — must be called via asyncio.to_thread()."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


async def get_password_hash(password: str) -> str:
    """Async-safe bcrypt hash (runs in thread pool)."""
    return await asyncio.to_thread(_hash_password_sync, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Async-safe bcrypt verify (runs in thread pool)."""
    return await asyncio.to_thread(_verify_password_sync, plain_password, hashed_password)


# ── Phone normalisation ───────────────────────────────────────

def normalize_phone(phone: str | None) -> str:
    """Normalize phone number to strict E.164 format (+998XXXXXXXXX)."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 9:
        return f"+998{digits}"
    return f"+{digits}" if digits else ""


# ── User queries ─────────────────────────────────────────────

async def get_or_create_user(
    session: AsyncSession,
    tg_user_id: int,
    full_name: str | None,
    role: UserRole,
    lang_code: str = "uz",
) -> User:
    """Return existing user or create a new one. Does NOT commit."""
    stmt = select(User).where(User.tg_user_id == tg_user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            tg_user_id=tg_user_id,
            full_name=full_name,
            role=role,
            lang_code=lang_code,
        )
        session.add(user)
        await session.flush()
    return user


async def get_user_by_tg_id(session: AsyncSession, tg_user_id: int) -> User | None:
    stmt = select(User).where(User.tg_user_id == tg_user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ── Invite code / Access request validation ───────────────────

async def validate_teacher_pin(session: AsyncSession, code: str) -> TeacherInviteCode | None:
    """Check if invite code is valid, active, and not expired."""
    stmt = select(TeacherInviteCode).where(
        TeacherInviteCode.code == code,
        TeacherInviteCode.is_active.is_(True),
    )
    result = await session.execute(stmt)
    invite = result.scalar_one_or_none()
    if invite is None:
        return None
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        return None
    return invite


async def validate_access_password(session: AsyncSession, password: str) -> AccessRequest | None:
    """Validate a teacher access password against approved requests.

    Bcrypt verification is run in a thread pool to avoid blocking the event loop.
    Only rows with status='approved' are checked (indexed column).
    """
    stmt = select(AccessRequest).where(AccessRequest.status == "approved")
    result = await session.execute(stmt)
    requests_list = result.scalars().all()

    # Iterate and verify — bcrypt is offloaded to thread pool
    for req in requests_list:
        if req.password:
            is_valid = await verify_password(password, req.password)
            if is_valid:
                return req
    return None


async def get_access_request_by_phone(
    session: AsyncSession, phone_number: str
) -> AccessRequest | None:
    """Find the latest access request by normalized phone number.

    Uses the indexed phone_number column for fast lookup.
    """
    clean_phone = normalize_phone(phone_number)

    stmt = (
        select(AccessRequest)
        .where(AccessRequest.phone_number == clean_phone)
        .order_by(AccessRequest.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_access_request(
    session: AsyncSession,
    tg_user_id: int,
    full_name: str,
    tg_username: str | None,
    phone_number: str,
    password: str | None = None,
) -> AccessRequest:
    """Create a new pending access request. Does NOT commit."""
    hashed_pw = await get_password_hash(password) if password else None
    req = AccessRequest(
        tg_user_id=tg_user_id,
        full_name=full_name,
        tg_username=tg_username,
        phone_number=normalize_phone(phone_number),
        status="pending",
        password=hashed_pw,
    )
    session.add(req)
    await session.flush()
    return req
