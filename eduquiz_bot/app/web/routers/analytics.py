"""Analytics router with chart data."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessRequest, Attempt, Test, User, UserRole
from app.db.session import get_async_session
from app.web.routers.auth import get_current_admin

router = APIRouter()


class DashboardStats(BaseModel):
    total_users: int
    total_teachers: int
    total_students: int
    total_tests: int
    total_attempts: int
    pending_requests: int


class ChartPoint(BaseModel):
    date: str
    count: int


@router.get("/analytics/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Get dashboard statistics."""
    # Total users
    result = await session.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0

    # Teachers
    result = await session.execute(
        select(func.count(User.id)).where(User.role == UserRole.TEACHER)
    )
    total_teachers = result.scalar() or 0

    # Students
    result = await session.execute(
        select(func.count(User.id)).where(User.role == UserRole.STUDENT)
    )
    total_students = result.scalar() or 0

    # Tests
    result = await session.execute(select(func.count(Test.id)))
    total_tests = result.scalar() or 0

    # Attempts
    result = await session.execute(select(func.count(Attempt.id)))
    total_attempts = result.scalar() or 0

    # Pending requests
    result = await session.execute(
        select(func.count(AccessRequest.id)).where(AccessRequest.status == "pending")
    )
    pending_requests = result.scalar() or 0

    return DashboardStats(
        total_users=total_users,
        total_teachers=total_teachers,
        total_students=total_students,
        total_tests=total_tests,
        total_attempts=total_attempts,
        pending_requests=pending_requests,
    )


@router.get("/analytics/user-growth", response_model=list[ChartPoint])
async def user_growth(
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    days: int = 30,
):
    """Get user registration growth over time."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = (
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        ChartPoint(date=str(row.date), count=row.count)
        for row in rows
    ]


@router.get("/analytics/activity", response_model=list[ChartPoint])
async def test_activity(
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    days: int = 30,
):
    """Get test attempt activity over time."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = (
        select(
            func.date(Attempt.started_at).label("date"),
            func.count(Attempt.id).label("count"),
        )
        .where(Attempt.started_at >= start_date)
        .group_by(func.date(Attempt.started_at))
        .order_by(func.date(Attempt.started_at))
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        ChartPoint(date=str(row.date), count=row.count)
        for row in rows
    ]
