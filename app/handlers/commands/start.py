from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.repositories.users import UserRepository
from app.repositories.uow import UnitOfWork
from app.services.users import UserService
from app.ui.keyboards import main_menu_kb
from app.ui.messages import main_menu_greeting, vacation_status
from app.domain.enums.user import UserGlobalStatus


router = Router(name="start")


@router.message(CommandStart())
async def start_cmd(message: Message, uow: UnitOfWork) -> None:
    user_vacation = UserGlobalStatus.ACTIVE
    
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]
        await uow.session.flush()
        
        user = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
        if user:
            user_vacation = user.global_status
    
    await message.answer(
        main_menu_greeting(vacation_status(user_vacation)),
        reply_markup=main_menu_kb(vacation_status(user_vacation)),
    )

