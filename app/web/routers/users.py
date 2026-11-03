"""Users management router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
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

    class Config:
        from_attributes = True


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
        )
        for u in users
    ]
