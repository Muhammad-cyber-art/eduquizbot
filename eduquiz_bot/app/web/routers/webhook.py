"""Telegram Webhook router."""

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request, Header, HTTPException
import logging

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    """Handle incoming Telegram Webhook updates."""
    # Derive the expected secret — first 32 alphanumeric chars of the token
    expected_secret = settings.BOT_TOKEN.replace(":", "")[:32]

    # In production (webhook mode), the secret header is MANDATORY
    if settings.WEBHOOK_URL:
        if not x_telegram_bot_api_secret_token:
            logger.warning("Webhook request missing secret token header")
            raise HTTPException(status_code=401, detail="Missing secret token")
        if x_telegram_bot_api_secret_token != expected_secret:
            logger.warning("Webhook request has invalid secret token")
            raise HTTPException(status_code=401, detail="Invalid secret token")
    elif x_telegram_bot_api_secret_token and x_telegram_bot_api_secret_token != expected_secret:
        # In polling/dev mode — validate if header is present, but don't require it
        raise HTTPException(status_code=401, detail="Invalid secret token")

    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp

    if not bot or not dp:
        logger.error("Bot or Dispatcher not initialized in FastAPI app state.")
        return {"status": "error", "detail": "Not initialized"}

    try:
        body = await request.body()
        update = Update.model_validate_json(body, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception:
        logger.exception("Failed to handle update")
        raise HTTPException(status_code=500, detail="Internal server error")
