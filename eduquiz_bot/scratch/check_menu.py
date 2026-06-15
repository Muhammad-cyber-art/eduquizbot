import asyncio
from app.config import settings
from aiogram import Bot

async def main():
    session = None
    if settings.PROXY_URL:
        from aiohttp_socks import ProxyConnector
        connector = ProxyConnector.from_url(settings.PROXY_URL)
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession(connector=connector)
        print("Using proxy:", settings.PROXY_URL)
        
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    try:
        chat_id = 1681742626
        btn = await bot.get_chat_menu_button(chat_id=chat_id)
        print("Menu button for chat", chat_id, ":", btn)
        
        default_btn = await bot.get_chat_menu_button()
        print("Default menu button:", default_btn)
    except Exception as e:
        print("Error:", e)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
