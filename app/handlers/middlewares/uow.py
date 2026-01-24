from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.uow import UnitOfWork


class UnitOfWorkMiddleware(BaseMiddleware):
    """
    Creates a fresh UnitOfWork per update and injects it into handler data.
    """

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self._sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["uow"] = UnitOfWork(self._sessionmaker)
        return await handler(event, data)

