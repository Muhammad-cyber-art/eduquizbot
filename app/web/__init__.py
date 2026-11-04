"""FastAPI admin panel application."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.web.routers import analytics, auth, requests, users

app = FastAPI(
    title="EduQuiz Admin Panel",
    version="1.0.0",
    docs_url="/api/docs",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(requests.router, prefix="/api", tags=["requests"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve built React frontend if dist folder exists
dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return """
        <html>
            <head>
                <title>EduQuiz Bot & Admin API</title>
                <style>
                    body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }
                    .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 450px; }
                    h1 { color: #1a73e8; margin-bottom: 0.5rem; }
                    p { color: #555; }
                    a { display: inline-block; margin-top: 1rem; padding: 10px 20px; background: #1a73e8; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }
                    a:hover { background: #1558b0; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>EduQuiz Bot & API</h1>
                    <p>EduQuiz Telegram Bot va FastAPI Admin tizimi 24/7 rejimda muvaffaqiyatli ishlamoqda.</p>
                    <a href="/api/docs">Swagger API Docs</a>
                </div>
            </body>
        </html>
        """
