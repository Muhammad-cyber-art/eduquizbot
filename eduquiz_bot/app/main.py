"""EduQuiz Bot — main entry point (aiogram 3 + FastAPI admin panel).

Startup order:
  1. Setup logging
  2. Configure proxy (optional)
  3. Init bot + DB
  4. Configure Telegram menu button
  5. Setup FSM storage (Redis → MemoryStorage fallback)
  6. Register handlers
  7. Start timer supervisor task
  8. Start uvicorn (FastAPI)
  9. Start polling OR register webhook

Shutdown:
  SIGTERM / SIGINT → cancel all tasks → close bot session → log clean exit.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import uvicorn

from app.config import settings
from app.db.session import engine, init_db
from app.handlers.common import router as common_router
from app.handlers.teacher import router as teacher_router
from app.handlers.student import router as student_router
from app.handlers.errors import router as errors_router
from app.services.timers import run_timer_loop
from app.web import app as web_app


# ── Logging ──────────────────────────────────────────────────

def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Silence noisy libraries in production
    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("aiogram.event").setLevel(logging.WARNING)


# ── Web server ───────────────────────────────────────────────

async def run_web_server() -> None:
    """Run FastAPI admin panel + WebApp API server."""
    config = uvicorn.Config(
        web_app,
        host="0.0.0.0",
        port=settings.PORT,
        log_level="warning" if settings.is_production else "info",
        # Disable uvicorn's own signal handlers — we manage them ourselves
        # so that graceful shutdown works correctly in asyncio.gather()
        lifespan="on",
    )
    server = uvicorn.Server(config)
    # Prevent uvicorn from installing its own SIGTERM/SIGINT handlers
    server.install_signal_handlers = lambda: None
    await server.serve()


# ── Timer supervisor ─────────────────────────────────────────

async def timer_supervisor(interval: int = 30) -> None:
    """Run the timer loop with automatic restart on unexpected failure."""
    logger = logging.getLogger(__name__ + ".timer")
    backoff = 5  # seconds between retries
    while True:
        try:
            await run_timer_loop(interval=interval)
        except asyncio.CancelledError:
            logger.info("Timer supervisor cancelled — shutting down.")
            raise
        except Exception:
            logger.exception(
                "Timer loop crashed unexpectedly. Restarting in %ds.", backoff
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 120)  # exponential backoff, cap at 2 min


# ── Main ─────────────────────────────────────────────────────

async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting EduQuiz Bot + Admin Panel…")

    # ── Proxy (optional) ──────────────────────────────────────
    session = None
    if settings.PROXY_URL:
        from aiohttp_socks import ProxyConnector
        from aiogram.client.session.aiohttp import AiohttpSession
        connector = ProxyConnector.from_url(settings.PROXY_URL)
        session = AiohttpSession(connector=connector)
        logger.info("Using SOCKS proxy: %s", settings.PROXY_URL)

    # ── Bot ──────────────────────────────────────────────────
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    # ── Database ─────────────────────────────────────────────
    try:
        await init_db()
        logger.info("Database connection established. Tables verified / created.")
    except Exception as db_err:
        logger.critical("🚨 Database ulanishida xatolik: %s. \nServer to'xtatilmoqda...", db_err)
        sys.exit(1)

    # ── Telegram WebApp menu button ───────────────────────────
    try:
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Natijalarim",
                web_app=WebAppInfo(url=f"{settings.WEB_URL}/webapp/student"),
            )
        )
        logger.info("Default WebApp menu button configured.")
    except Exception as e:
        logger.warning("Failed to set default menu button: %s", e)

    # ── FSM Storage: Redis with MemoryStorage fallback ────────
    storage: MemoryStorage | object = MemoryStorage()
    try:
        from aiogram.fsm.storage.redis import RedisStorage as AiogramRedisStorage
        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            decode_responses=False,
        )
        await redis_client.ping()
        storage = AiogramRedisStorage(redis=redis_client)
        logger.info("FSM storage: Redis (%s)", settings.REDIS_URL)
    except Exception as redis_err:
        logger.warning(
            "Redis unavailable (%s) — falling back to MemoryStorage. "
            "FSM state will be lost on restart!",
            redis_err,
        )

    # ── Dispatcher ───────────────────────────────────────────
    dp = Dispatcher(storage=storage)
    dp.include_router(common_router)
    dp.include_router(teacher_router)
    dp.include_router(student_router)
    dp.include_router(errors_router)

    # ── Share bot/dp with FastAPI via app state ───────────────
    web_app.state.bot = bot
    web_app.state.dp = dp

    logger.info("Admin API available at http://localhost:%s/api/docs", settings.PORT)

    # ── Role checking ────────────────────────────────────────
    role = os.getenv("PROCESS_ROLE", "all").lower()

    # ── Background tasks ─────────────────────────────────────
    timer_task = None
    web_task = None
    if role in ("all", "web"):
        timer_task = asyncio.create_task(timer_supervisor(interval=30), name="timer_supervisor")
        web_task = asyncio.create_task(run_web_server(), name="web_server")
        logger.info("Started WEB tasks (FastAPI + Timers)")

    # ── Graceful shutdown helper ──────────────────────────────
    shutdown_event = asyncio.Event()

    def _handle_signal(sig: signal.Signals) -> None:
        logger.info("Received %s — initiating graceful shutdown…", sig.name)
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _handle_signal, sig)
        except (NotImplementedError, OSError):
            # Windows does not support add_signal_handler for all signals
            pass

    # ── Bot start mode: webhook or polling ────────────────────
    try:
        if settings.WEBHOOK_URL and role in ("all", "web"):
            # ─── WEBHOOK MODE ─────────────────────────────────
            webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
            logger.info("Webhook mode: registering %s", webhook_url)
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                secret_token=settings.WEBHOOK_SECRET,
                allowed_updates=dp.resolve_used_update_types(),
            )
            logger.info("Webhook registered. Waiting for shutdown signal…")
            await shutdown_event.wait()
            
        elif role in ("all", "bot"):
            # ─── POLLING MODE ─────────────────────────────────
            logger.info("Polling mode: deleting webhook and starting polling.")
            await bot.delete_webhook(drop_pending_updates=True)

            polling_task = asyncio.create_task(
                dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
                name="polling",
            )
            logger.info("Started BOT task (Aiogram Polling)")

            # Wait for either shutdown signal or task failure
            tasks_to_wait = [polling_task, asyncio.create_task(shutdown_event.wait())]
            if web_task:
                tasks_to_wait.append(web_task)
                
            done, pending = await asyncio.wait(
                tasks_to_wait,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                if task.exception():
                    logger.error("Task %s failed: %s", task.get_name(), task.exception())
                    
        else:
            logger.info("Web-only mode without Webhooks. Waiting for shutdown signal...")
            tasks_to_wait = [asyncio.create_task(shutdown_event.wait())]
            if web_task:
                tasks_to_wait.append(web_task)
            await asyncio.wait(tasks_to_wait, return_when=asyncio.FIRST_COMPLETED)

    except asyncio.CancelledError:
        logger.info("Main task cancelled.")
    finally:
        logger.info("Shutting down…")

        # Cancel all background tasks
        tasks_to_cancel = []
        if timer_task and not timer_task.done():
            tasks_to_cancel.append(timer_task)
        if web_task and not web_task.done():
            tasks_to_cancel.append(web_task)
        if 'polling_task' in locals() and polling_task and not polling_task.done():
            tasks_to_cancel.append(polling_task)
            
        for task in tasks_to_cancel:
            task.cancel()

        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

        # Dispose DB connection pool
        await engine.dispose()
        logger.info("Database connection pool closed.")

        # Close bot HTTP session
        await bot.session.close()
        logger.info("Bot stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
