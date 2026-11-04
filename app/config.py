"""Application configuration via environment variables."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    BOT_TOKEN: str

    # Proxy for Telegram API (e.g. socks5://user:pass@host:port)
    # Leave empty to use direct connection (needs VPN in blocked regions)
    PROXY_URL: str = ""

    # PostgreSQL (asyncpg DSN) — or SQLite for local dev
    DATABASE_URL: str = "sqlite+aiosqlite:///./eduquiz.db"

    # Redis (FSM storage & caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    # App
    LANG_DEFAULT: str = "uz"
    LOG_LEVEL: str = "INFO"

    # Admin Panel
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    JWT_SECRET: str = "eduquiz-secret-key-change-in-production"
    WEB_PORT: int = int(os.environ.get("PORT", os.environ.get("WEB_PORT", 7860)))


settings = Settings()
