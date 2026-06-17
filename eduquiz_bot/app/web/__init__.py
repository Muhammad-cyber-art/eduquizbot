"""FastAPI admin panel + WebApp API application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.web.routers import analytics, auth, requests, users, webapp, webhook

logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    logger.info(
        "FastAPI starting. CORS origins: %s",
        [o for o in _build_cors_origins()],
    )
    yield
    # Dispose the engine connection pool on shutdown (if owned by this process)
    # In most cases, main.py disposes it; this is a belt-and-suspenders guard.
    try:
        from app.db.session import engine
        await engine.dispose()
        logger.info("DB connection pool disposed from FastAPI lifespan.")
    except Exception as e:
        logger.warning("Error disposing engine in lifespan: %s", e)


# ── CORS ─────────────────────────────────────────────────────

def _build_cors_origins() -> list[str]:
    """Build the list of allowed CORS origins from current settings.

    Called at app creation time — by then Docker has injected all env vars,
    so settings values are final and correct.
    """
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:80",
        "http://localhost",
    ]
    if settings.WEB_URL and settings.WEB_URL not in origins:
        origins.append(settings.WEB_URL)
    return origins


# ── App factory ───────────────────────────────────────────────

app = FastAPI(
    title="EduQuiz Admin Panel",
    version="1.0.0",
    lifespan=lifespan,
    # Disable Swagger / ReDoc in production to reduce attack surface
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None if settings.is_production else "/api/redoc",
    openapi_url=None if settings.is_production else "/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-TG-Init-Data"],
)

# ── Routers ───────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(requests.router, prefix="/api", tags=["requests"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(webapp.router, prefix="/api/webapp", tags=["webapp"])
app.include_router(webhook.router, prefix=settings.WEBHOOK_PATH, tags=["webhook"])


# ── Health check ─────────────────────────────────────────────

@app.get("/api/health", tags=["system"])
async def health():
    """Health check endpoint.

    Verifies database connectivity. Returns 200 if healthy, 503 if degraded.
    Used by Docker healthchecks and load balancers.
    """
    from app.db.session import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error("Health check: database unreachable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "database": "disconnected",
                "error": str(exc),
            },
        )
