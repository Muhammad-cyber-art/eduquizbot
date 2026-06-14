"""Users management router."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserRole
from app.db.session import get_async_session
from app.web.routers.auth import get_current_admin

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    tg_user_id: int
    full_name: str | None
    role: UserRole
    lang_code: str
    created_at: str
    max_tests: int
    max_students: int
    is_active: bool
    ai_queries_limit: int
    ai_queries_used: int
    expires_at: str | None = None

    class Config:
        from_attributes = True


class UserLimitsUpdate(BaseModel):
    max_tests: int | None = None
    max_students: int | None = None
    is_active: bool | None = None
    ai_queries_limit: int | None = None
    ai_queries_used: int | None = None
    expires_at: datetime | None = None



@router.get("/users", response_model=list[UserResponse])
async def list_users(
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    role: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List all users with optional filters."""
    stmt = select(User).order_by(User.created_at.desc())
    
    if role:
        stmt = stmt.where(User.role == role)
    
    if search:
        stmt = stmt.where(User.full_name.ilike(f"%{search}%"))
    
    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=u.id,
            tg_user_id=u.tg_user_id,
            full_name=u.full_name,
            role=u.role,
            lang_code=u.lang_code,
            created_at=u.created_at.isoformat() if u.created_at else "",
            max_tests=u.max_tests,
            max_students=u.max_students,
            is_active=u.is_active,
            ai_queries_limit=u.ai_queries_limit,
            ai_queries_used=u.ai_queries_used,
            expires_at=u.expires_at.isoformat() if u.expires_at else None,
        )
        for u in users
    ]



@router.put("/users/{user_id}/limits", response_model=UserResponse)
async def update_user_limits(
    user_id: int,
    request: UserLimitsUpdate,
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Update teacher limits and active status."""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if request.max_tests is not None:
        user.max_tests = request.max_tests
    if request.max_students is not None:
        user.max_students = request.max_students
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.ai_queries_limit is not None:
        user.ai_queries_limit = request.ai_queries_limit
    if request.ai_queries_used is not None:
        user.ai_queries_used = request.ai_queries_used
    if request.expires_at is not None:
        user.expires_at = request.expires_at
    elif "expires_at" in request.model_fields_set:
        user.expires_at = None
        
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        tg_user_id=user.tg_user_id,
        full_name=user.full_name,
        role=user.role,
        lang_code=user.lang_code,
        created_at=user.created_at.isoformat() if user.created_at else "",
        max_tests=user.max_tests,
        max_students=user.max_students,
        is_active=user.is_active,
        ai_queries_limit=user.ai_queries_limit,
        ai_queries_used=user.ai_queries_used,
        expires_at=user.expires_at.isoformat() if user.expires_at else None,
    )

