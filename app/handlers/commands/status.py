from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.domain.exceptions import DomainError
from app.repositories.users import UserRepository
from app.repositories.uow import UnitOfWork
from app.services.users import UserService


router = Router(name="status")


@router.message(Command("vacation_on"))
async def vacation_on(message: Message, uow: UnitOfWork) -> None:
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]
        try:
            await UserService(user_repo).set_vacation(message.from_user.id, enabled=True)  # type: ignore[union-attr]
        except DomainError as e:
            await message.answer(f"❌ {e}")
            return
    await message.answer("🌴 Vacation enabled. You will not receive event notifications.")


@router.message(Command("vacation_off"))
async def vacation_off(message: Message, uow: UnitOfWork) -> None:
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]
        try:
            await UserService(user_repo).set_vacation(message.from_user.id, enabled=False)  # type: ignore[union-attr]
        except DomainError as e:
            await message.answer(f"❌ {e}")
            return
    await message.answer("✅ Vacation disabled.")

