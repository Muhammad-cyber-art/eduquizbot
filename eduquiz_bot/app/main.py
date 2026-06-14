"""EduQuiz Bot — main entry point (aiogram 3 + FastAPI admin panel)."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import uvicorn

from app.config import settings
from app.db.session import init_db
from app.handlers.common import router as common_router
from app.handlers.teacher import router as teacher_router
from app.handlers.student import router as student_router
from app.services.timers import run_timer_loop
from app.web import app as web_app


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def run_web_server() -> None:
    """Run FastAPI admin panel server."""
    config = uvicorn.Config(
        web_app,
        host="0.0.0.0",
        port=settings.WEB_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting EduQuiz Bot + Admin Panel...")

    # Configure proxy if set (bypasses regional Telegram API blocks)
    session = None
    if settings.PROXY_URL:
        from aiohttp_socks import ProxyConnector
        connector = ProxyConnector.from_url(settings.PROXY_URL)
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession(connector=connector)
        logger.info("Using proxy: %s", settings.PROXY_URL)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    # Auto-create tables
    await init_db()
    logger.info("Database initialized.")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers (order matters: common first)
    dp.include_router(common_router)
    dp.include_router(teacher_router)
    dp.include_router(student_router)

    # Start background tasks
    timer_task = asyncio.create_task(run_timer_loop(interval=30))
    web_task = asyncio.create_task(run_web_server())
    
    logger.info(f"Admin panel available at http://localhost:{settings.WEB_PORT}/api/docs")

    try:
        logger.info("Polling started.")
        # Delete webhook and drop backlogged updates to avoid start-up overload
        await bot.delete_webhook(drop_pending_updates=True)
        # Run both bot and web server concurrently
        await asyncio.gather(
            dp.start_polling(bot),
            web_task,
        )
    except asyncio.CancelledError:
        pass
    finally:
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
