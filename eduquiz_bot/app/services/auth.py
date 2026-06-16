"""Authentication & user management service."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessRequest, TeacherInviteCode, User, UserRole

# Hashing konfiguratsiyasi (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def normalize_phone(phone: str | None) -> str:
    """Telefon raqamni qat'iy E.164 formatiga normalizatsiya qilish."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 9:
        return f"+998{digits}"
    return f"+{digits}" if digits else ""

async def get_or_create_user(
    session: AsyncSession,
    tg_user_id: int,
    full_name: str | None,
    role: UserRole,
    lang_code: str = "uz",
) -> User:
    """Return existing user or create a new one. (No internal commits)"""
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
        await session.flush() # Transaction yopilmaydi, faqat DB ga yoziladi
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
    """Check if password matches an approved access request using bcrypt verification."""
    stmt = select(AccessRequest).where(AccessRequest.status == "approved")
    result = await session.execute(stmt)
    requests = result.scalars().all()
    
    # Hashed parollar bilan xavfsiz tekshirish
    for req in requests:
        if req.password and verify_password(password, req.password):
            return req
    return None


async def get_access_request_by_phone(session: AsyncSession, phone_number: str) -> AccessRequest | None:
    """Find the latest access request by normalized phone number (Full Table Scan oldi olindi)."""
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
    """Create a new pending access request. (No internal commits)"""
    hashed_pw = get_password_hash(password) if password else None
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
