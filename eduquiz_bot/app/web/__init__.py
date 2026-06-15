"""FastAPI admin panel application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.web.routers import analytics, auth, requests, users, webapp, webhook

app = FastAPI(
    title="EduQuiz Admin Panel",
    version="1.0.0",
    docs_url="/api/docs",
)

from app.config import settings

# CORS for React frontend
app.add_middleware(

    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", settings.WEB_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
