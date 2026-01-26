"""Admin access check middleware."""
from __future__ import annotations

from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.repositories.uow import UnitOfWork
from app.repositories.users import UserRepository


async def is_admin(user_id: int, uow: UnitOfWork) -> bool:
    """Check if user has admin rights."""
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        user = await user_repo.get(user_id)
        return user.is_admin if user else False


class AdminOnlyMiddleware(BaseMiddleware):
    """Middleware that allows only admins to proceed."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        if not user_id:
            return await handler(event, data)
        
        uow = data.get("uow")
        if not uow:
            return await handler(event, data)
        
        if not await is_admin(user_id, uow):
            if isinstance(event, Message):
                await event.answer("⛔️ Доступ запрещён. Команда только для администраторов.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔️ Доступ запрещён.", show_alert=True)
            return
        
        return await handler(event, data)
