"""Telegram Webhook router."""

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request, Header, HTTPException
import logging

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(None)):
    """Handle incoming Telegram Webhook updates."""
    # Security check (optional, set via bot.set_webhook(secret_token=...))
    # We will use the bot token's first 32 chars as a simple secret token if needed
    expected_secret = settings.BOT_TOKEN.replace(":", "")[:32]
    if x_telegram_bot_api_secret_token and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid secret token")

    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp

    if not bot or not dp:
        logger.error("Bot or Dispatcher not initialized in FastAPI app state.")
        return {"status": "error", "detail": "Not initialized"}

    # Validate and parse Update
    try:
        body = await request.body()
        update = Update.model_validate_json(body, context={"bot": bot})
        # Feed the update to aiogram dispatcher
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Failed to handle update")
        raise HTTPException(status_code=500, detail="Internal server error")
