"""Access requests management router."""

import secrets
import string
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessRequest
from app.db.session import get_async_session
from app.web.routers.auth import get_current_admin

router = APIRouter()


class AccessRequestResponse(BaseModel):
    id: int
    tg_user_id: int
    full_name: str
    tg_username: str | None
    phone_number: str | None
    status: str
    password: str | None
    created_at: datetime
    reviewed_at: datetime | None

    class Config:
        from_attributes = True


class ApproveResponse(BaseModel):
    id: int
    password: str
    status: str


def generate_password(length: int = 8) -> str:
    """Generate a random password."""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


@router.get("/requests", response_model=list[AccessRequestResponse])
async def list_requests(
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    status_filter: str = "all",
):
    """List access requests. Filter: all, pending, approved, rejected."""
    if status_filter == "all":
        stmt = select(AccessRequest).order_by(AccessRequest.created_at.desc())
    else:
        stmt = (
            select(AccessRequest)
            .where(AccessRequest.status == status_filter)
            .order_by(AccessRequest.created_at.desc())
        )
    result = await session.execute(stmt)
    requests = result.scalars().all()
    return [AccessRequestResponse.model_validate(r) for r in requests]


@router.post("/requests/{request_id}/approve", response_model=ApproveResponse)
async def approve_request(
    request_id: int,
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Approve an access request and generate a password."""
    stmt = select(AccessRequest).where(AccessRequest.id == request_id)
    result = await session.execute(stmt)
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
    
    password = generate_password()
    req.status = "approved"
    req.password = password
    req.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    
    return ApproveResponse(id=req.id, password=password, status="approved")


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    admin: Annotated[str, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Reject an access request."""
    stmt = select(AccessRequest).where(AccessRequest.id == request_id)
    result = await session.execute(stmt)
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
    
    req.status = "rejected"
    req.reviewed_at = datetime.now(timezone.utc)
    await session.commit()
    
    return {"id": req.id, "status": "rejected"}
