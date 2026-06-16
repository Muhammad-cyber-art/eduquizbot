"""FastAPI admin panel application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.web.routers import analytics, auth, requests, users, webapp, webhook

# Disable Swagger/ReDoc in production to avoid exposing API docs
app = FastAPI(
    title="EduQuiz Admin Panel",
    version="1.0.0",
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None if settings.is_production else "/api/redoc",
    openapi_url=None if settings.is_production else "/api/openapi.json",
)

# CORS — restrict allowed origins in production
_allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if settings.WEB_URL and settings.WEB_URL not in _allowed_origins:
    _allowed_origins.append(settings.WEB_URL)
if settings.WEBHOOK_URL and settings.WEBHOOK_URL not in _allowed_origins:
    _allowed_origins.append(settings.WEBHOOK_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-TG-Init-Data"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(requests.router, prefix="/api", tags=["requests"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(webapp.router, prefix="/api/webapp", tags=["webapp"])
app.include_router(webhook.router, prefix=settings.WEBHOOK_PATH, tags=["webhook"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
