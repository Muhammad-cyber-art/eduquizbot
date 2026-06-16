"""Admin authentication router with rate limiting."""

import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Annotated

import hmac
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------------------------------------------------------------------------
# Simple in-memory rate limiter for login endpoint
# Tracks failed attempts per IP: {ip: [(timestamp, ...), ...]}
# ---------------------------------------------------------------------------
_login_attempts: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW = 60        # seconds
_MAX_ATTEMPTS = 5        # max failed attempts in window
_BLOCK_DURATION = 300    # block for 5 minutes after exceeding limit
_blocked_until: dict[str, float] = {}


def _check_rate_limit(ip: str) -> None:
    now = time.monotonic()

    # Check if currently blocked
    if ip in _blocked_until:
        if now < _blocked_until[ip]:
            retry_after = int(_blocked_until[ip] - now)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )
        else:
            del _blocked_until[ip]
            _login_attempts[ip] = []

    # Remove old attempts outside window
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < _RATE_WINDOW]


def _record_failure(ip: str) -> None:
    now = time.monotonic()
    _login_attempts[ip].append(now)
    if len(_login_attempts[ip]) >= _MAX_ATTEMPTS:
        _blocked_until[ip] = now + _BLOCK_DURATION
        _login_attempts[ip] = []


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")


async def get_current_admin(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """Validate JWT and return admin username."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/auth/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    """Admin login endpoint with brute-force protection."""
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit before processing
    _check_rate_limit(client_ip)

    is_username_valid = hmac.compare_digest(body.username, settings.ADMIN_USERNAME)
    is_password_valid = hmac.compare_digest(body.password, settings.ADMIN_PASSWORD)

    if not (is_username_valid and is_password_valid):
        _record_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Success — clear any previous failures for this IP
    _login_attempts[client_ip] = []

    token = create_access_token({"sub": body.username})
    return TokenResponse(access_token=token)


@router.get("/auth/me")
async def me(admin: Annotated[str, Depends(get_current_admin)]):
    """Get current admin info."""
    return {"username": admin, "role": "admin"}
