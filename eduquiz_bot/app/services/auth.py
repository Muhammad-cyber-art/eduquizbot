"""Authentication & user management service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessRequest, TeacherInviteCode, User, UserRole


async def get_or_create_user(
    session: AsyncSession,
    tg_user_id: int,
    full_name: str | None,
    role: UserRole,
    lang_code: str = "uz",
) -> User:
    """Return existing user or create a new one."""
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
        await session.commit()
        await session.refresh(user)
    return user


async def get_user_by_tg_id(session: AsyncSession, tg_user_id: int) -> User | None:
    stmt = select(User).where(User.tg_user_id == tg_user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


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
    """Check if password matches an approved access request."""
    stmt = select(AccessRequest).where(
        AccessRequest.password == password,
        AccessRequest.status == "approved",
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_access_request_by_phone(session: AsyncSession, phone_number: str) -> AccessRequest | None:
    """Find the latest access request by phone number."""
    # Strip plus signs and spaces to check normalization
    clean_phone = phone_number.replace("+", "").replace(" ", "").strip()
    
    # We will search by exact match, or try both with and without plus sign
    stmt = (
        select(AccessRequest)
        .where(
            (AccessRequest.phone_number == phone_number) | 
            (AccessRequest.phone_number == clean_phone) |
            (AccessRequest.phone_number == f"+{clean_phone}")
        )
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
) -> AccessRequest:
    """Create a new pending access request."""
    req = AccessRequest(
        tg_user_id=tg_user_id,
        full_name=full_name,
        tg_username=tg_username,
        phone_number=phone_number,
        status="pending",
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req

