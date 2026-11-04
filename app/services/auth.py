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


async def validate_teacher_pin(session: AsyncSession, code: str) -> bool:
    """Check if invite code is valid, active, and not expired."""
    stmt = select(TeacherInviteCode).where(
        TeacherInviteCode.code == code,
        TeacherInviteCode.is_active.is_(True),
    )
    result = await session.execute(stmt)
    invite = result.scalar_one_or_none()
    if invite is None:
        return False
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        return False
    return True


async def validate_access_password(session: AsyncSession, password: str) -> AccessRequest | None:
    """Check if password matches an approved access request."""
    stmt = select(AccessRequest).where(
        AccessRequest.password == password,
        AccessRequest.status == "approved",
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
