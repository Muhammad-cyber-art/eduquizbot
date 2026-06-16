"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    BOT_TOKEN: str

    # Proxy for Telegram API (e.g. socks5://user:pass@host:port)
    PROXY_URL: str = ""

    # PostgreSQL (asyncpg DSN)
    DATABASE_URL: str = "sqlite+aiosqlite:///./eduquiz.db"

    # Redis (FSM storage & caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str = "/api/webhook"

    # App
    LANG_DEFAULT: str = "uz"
    LOG_LEVEL: str = "INFO"
    APP_ENV: str = "development"  # "development" | "production"

    # Admin Panel — MUST be overridden in production via environment variables
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str  # No default — required in .env
    JWT_SECRET: str      # No default — required in .env
    WEB_PORT: int = 8001

    GEMINI_API_KEY: str = ""
    WEB_URL: str = "http://localhost:5173"

    # Telegram Chat ID of the admin user (for access request notifications)
    # Get your chat ID by messaging @userinfobot in Telegram
    # Leave empty to disable notifications
    ADMIN_CHAT_ID: str = ""  # stored as str; converted to int in property below

    @property
    def admin_chat_id(self) -> int | None:
        """Return ADMIN_CHAT_ID as int, or None if not set."""
        try:
            return int(self.ADMIN_CHAT_ID) if self.ADMIN_CHAT_ID.strip() else None
        except (ValueError, TypeError):
            return None

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
