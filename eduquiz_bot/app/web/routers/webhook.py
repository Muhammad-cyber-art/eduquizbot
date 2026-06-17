"""Telegram Webhook router — receives updates from Telegram's servers."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request
from fastapi import Header

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict:
    """Handle incoming Telegram Webhook updates.

    Validates the X-Telegram-Bot-Api-Secret-Token header against
    WEBHOOK_SECRET before processing any update.
    """
    expected_secret = settings.WEBHOOK_SECRET

    # In production (webhook mode), the secret header is mandatory
    if settings.WEBHOOK_URL:
        if not x_telegram_bot_api_secret_token:
            logger.warning(
                "Webhook request rejected: missing X-Telegram-Bot-Api-Secret-Token header. "
                "Possible scan/probe from IP: %s",
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(status_code=401, detail="Missing secret token")
        if x_telegram_bot_api_secret_token != expected_secret:
            logger.warning(
                "Webhook request rejected: invalid secret token from IP: %s",
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(status_code=401, detail="Invalid secret token")
    elif x_telegram_bot_api_secret_token and x_telegram_bot_api_secret_token != expected_secret:
        # Development mode: validate if present, do not require it
        raise HTTPException(status_code=401, detail="Invalid secret token")

    bot: Bot | None = getattr(request.app.state, "bot", None)
    dp: Dispatcher | None = getattr(request.app.state, "dp", None)

    if bot is None or dp is None:
        logger.error(
            "Webhook received but bot/dispatcher are not initialized in app.state. "
            "This should not happen after startup completes."
        )
        raise HTTPException(status_code=503, detail="Bot not initialized")

    try:
        body = await request.body()
        update = Update.model_validate_json(body, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception:
        logger.exception("Failed to process webhook update")
        raise HTTPException(status_code=500, detail="Internal server error")
