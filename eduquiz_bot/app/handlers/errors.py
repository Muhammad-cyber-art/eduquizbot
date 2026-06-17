"""Global error handler for the aiogram dispatcher."""

import logging
from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)
router = Router()

@router.errors()
async def global_error_handler(event: ErrorEvent):
    """Catch all unhandled exceptions in the dispatcher."""
    logger.exception("Unhandled exception triggered by update: %s", event.update.model_dump_json(exclude_none=True))

    # Try to notify the user if possible
    if event.update.message:
        try:
            await event.update.message.answer(
                "⚠️ Kechirasiz, tizimda kutilmagan xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."
            )
        except Exception as e:
            logger.error("Failed to send error message to user: %s", e)
    elif event.update.callback_query:
        try:
            await event.update.callback_query.answer(
                "Tizimda xatolik yuz berdi.", show_alert=True
            )
        except Exception as e:
            logger.error("Failed to send error alert to user: %s", e)
