"""Application configuration — PostgreSQL + Redis required.

DATABASE_URL is mandatory — no SQLite fallback in production.
All settings are loaded from .env. Missing required fields crash at startup (by design).
"""

import logging
import secrets
import sys
from pydantic import Field, field_validator, model_validator, ValidationInfo, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Telegram ─────────────────────────────────────────────
    BOT_TOKEN: str

    # SOCKS5/HTTP proxy (optional — for regions where Telegram is blocked)
    PROXY_URL: str = ""

    # ── Database (PostgreSQL — REQUIRED) ──────────────────────
    # Format: postgresql+asyncpg://user:password@host:5432/dbname
    # NEVER use sqlite+aiosqlite — SQLite is not supported in production.
    DATABASE_URL: str  # No default — crashes at startup if not set

    # ── Redis (REQUIRED for FSM state) ────────────────────────
    # Format: redis://:password@host:6379/0
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Webhook ──────────────────────────────────────────────
    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str = "/api/webhook"
    # Generate: python -c "import secrets; print(secrets.token_hex(32))"
    WEBHOOK_SECRET: str = ""

    # ── App ───────────────────────────────────────────────────
    LANG_DEFAULT: str = "uz"
    LOG_LEVEL: str = "INFO"
    APP_ENV: str = "development"  # "development" | "production"

    # ── Admin Panel ───────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str  # Required
    JWT_SECRET: str      # Required
    PORT: int = Field(default=8001, alias="PORT") # Cloud host dynamic port

    # ── Integrations ─────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    WEB_URL: str = "http://localhost:5173"

    # ── Notifications ─────────────────────────────────────────
    ADMIN_CHAT_ID: str = ""

    # ── Validators ────────────────────────────────────────────

    @field_validator("BOT_TOKEN", "ADMIN_PASSWORD", "JWT_SECRET", "DATABASE_URL", mode="after")
    @classmethod
    def check_not_empty(cls, v: str, info: ValidationInfo) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty or blank")
        return v

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def enforce_postgresql(cls, v: str) -> str:
        """Reject any non-PostgreSQL DATABASE_URL at startup."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                f"DATABASE_URL must use the 'postgresql+asyncpg://' scheme. "
                f"Got: '{v[:30]}...'. "
                f"SQLite and other databases are not supported. "
                f"Example: postgresql+asyncpg://eduquiz:password@db:5432/eduquiz"
            )
        return v

    @model_validator(mode="after")
    def ensure_webhook_secret(self) -> "Settings":
        """Warn loudly if WEBHOOK_SECRET is missing in webhook mode."""
        if not self.WEBHOOK_SECRET or len(self.WEBHOOK_SECRET) < 16:
            if self.WEBHOOK_URL:
                logger.error(
                    "WEBHOOK_SECRET is not set but WEBHOOK_URL is configured. "
                    "Generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            else:
                logger.warning("WEBHOOK_SECRET not set — generating ephemeral secret for this session.")
            object.__setattr__(self, "WEBHOOK_SECRET", secrets.token_hex(16))
        return self

    # ── Computed properties ───────────────────────────────────

    @property
    def admin_chat_id(self) -> int | None:
        try:
            return int(self.ADMIN_CHAT_ID) if self.ADMIN_CHAT_ID.strip() else None
        except ValueError as e:
            logger.error("Invalid ADMIN_CHAT_ID in config: %s", e)
            return None

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

try:
    settings = Settings()
except ValidationError as e:
    logger.critical("🚨 Kiritilgan muhit o'zgaruvchilari (.env) to'liq emas yoki noto'g'ri!")
    for err in e.errors():
        logger.critical(f"❌ Xato: {err['loc'][0]} - {err['msg']}")
    sys.exit(1)
