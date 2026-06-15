from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo
import logging

from app.config import settings
from app.db.models import UserRole

logger = logging.getLogger(__name__)

async def set_user_menu_button(bot: Bot, tg_user_id: int, role: UserRole) -> None:
    """Sets the dynamic chat menu button (WebApp button) next to the input field depending on the user's role."""
    try:
        if role == UserRole.TEACHER:
            url = f"{settings.WEB_URL}/webapp/teacher"
            text = "Mini App"
        else:
            url = f"{settings.WEB_URL}/webapp/student"
            text = "Natijalarim"
        
        logger.info("Setting WebApp menu button for user %s: url=%s, text=%s", tg_user_id, url, text)
        await bot.set_chat_menu_button(
            chat_id=tg_user_id,
            menu_button=MenuButtonWebApp(
                text=text,
                web_app=WebAppInfo(url=url)
            )
        )
    except Exception as e:
        logger.exception("Failed to set chat menu button for user %s: %s", tg_user_id, e)
