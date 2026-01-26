from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import load_settings
from app.di import build_container
from app.handlers.commands.rooms import router as rooms_router
from app.handlers.commands.start import router as start_router
from app.handlers.commands.status import router as status_router
from app.handlers.commands.events import router as events_router
from app.handlers.commands.admin import router as admin_router
from app.handlers.middlewares.uow import UnitOfWorkMiddleware
from app.handlers.callbacks.events import router as events_cb_router
from app.handlers.callbacks.rooms import router as rooms_cb_router
from app.handlers.callbacks.menu import router as menu_router


logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    settings = load_settings()
    container = build_container(settings)
    # BOT_TOKEN is intentionally read from env at runtime (never hardcode).
    bot = Bot(token=settings.bot_token)

    dp = Dispatcher()
    dp.update.middleware(UnitOfWorkMiddleware(container.sessionmaker))
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(rooms_router)
    dp.include_router(status_router)
    dp.include_router(events_router)
    dp.include_router(events_cb_router)
    dp.include_router(rooms_cb_router)
    dp.include_router(menu_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

