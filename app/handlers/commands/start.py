from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.repositories.users import UserRepository
from app.repositories.uow import UnitOfWork
from app.services.users import UserService
from app.ui.keyboards import main_menu_kb
from app.ui.messages import main_menu_greeting, vacation_status, help_message
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
        parse_mode="Markdown",
        reply_markup=main_menu_kb(vacation_status(user_vacation)),
    )


@router.message(Command("menu"))
async def menu_cmd(message: Message, uow: UnitOfWork) -> None:
    """Return to main menu from anywhere."""
    user_vacation = UserGlobalStatus.ACTIVE
    
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        user = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
        if user:
            user_vacation = user.global_status
    
    await message.answer(
        "🏠 Возвращаемся в главное меню!\n\nЧто будем делать дальше?",
        reply_markup=main_menu_kb(vacation_status(user_vacation)),
    )


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    """Show quick start guide."""
    await message.answer(help_message(), parse_mode="Markdown")


@router.message(Command("reset"))
async def reset_cmd(message: Message, state: FSMContext, uow: UnitOfWork) -> None:
    """Reset FSM state and return to main menu. Use this if bot is stuck in some state."""
    await state.clear()
    
    user_vacation = UserGlobalStatus.ACTIVE
    
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        user = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
        if user:
            user_vacation = user.global_status
    
    await message.answer(
        "🔄 Состояние очищено. Вы в главном меню.",
        reply_markup=main_menu_kb(vacation_status(user_vacation)),
    )


