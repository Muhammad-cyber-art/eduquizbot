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

    # Set default WebApp menu button on startup
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Natijalarim",
                web_app=WebAppInfo(url=f"{settings.WEB_URL}/webapp/student")
            )
        )
        logger.info("Default WebApp menu button configured successfully.")
    except Exception as e:
        logger.error("Failed to set default menu button on startup: %s", e)

    # FSM Storage: Redis if available, MemoryStorage as fallback
    storage = MemoryStorage()
    try:
        from aiogram.fsm.storage.redis import RedisStorage as AiogramRedisStorage
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await redis_client.ping()  # Test connection
        storage = AiogramRedisStorage(redis=redis_client)
        logger.info("FSM storage: Redis (%s)", settings.REDIS_URL)
    except Exception as redis_err:
        logger.warning("Redis unavailable (%s) — using MemoryStorage", redis_err)
    dp = Dispatcher(storage=storage)

    # Register routers (order matters: common first)
    dp.include_router(common_router)
    dp.include_router(teacher_router)
    dp.include_router(student_router)

    # Start background tasks
    timer_task = asyncio.create_task(run_timer_loop(interval=30))
    web_task = asyncio.create_task(run_web_server())
    
    # Store bot and dp in FastAPI app state for webhook routing
    web_app.state.bot = bot
    web_app.state.dp = dp

    logger.info(f"Admin panel available at http://localhost:{settings.WEB_PORT}/api/docs")

    try:
        if settings.WEBHOOK_URL:
            # --- WEBHOOK MODE ---
            webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
            logger.info(f"Webhook mode enabled. Setting webhook URL: {webhook_url}")
            secret_token = settings.BOT_TOKEN.replace(":", "")[:32]
            await bot.set_webhook(url=webhook_url, drop_pending_updates=True, secret_token=secret_token)
            
            # Just wait for the web server to finish (it will handle webhook POSTs)
            await web_task
        else:
            # --- POLLING MODE ---
            logger.info("Polling mode enabled. Deleting webhook.")
            await bot.delete_webhook(drop_pending_updates=True)
            
            logger.info("Polling started.")
            # Run both bot polling and web server concurrently
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
