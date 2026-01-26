from __future__ import annotations

import uuid
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.domain.exceptions import DomainError
from app.repositories.rooms import RoomMemberRepository, RoomRepository
from app.repositories.users import UserRepository
from app.repositories.uow import UnitOfWork
from app.services.rooms import RoomService
from app.services.users import UserService
from app.ui.messages import joined_room, room_created, room_invite_share
from app.ui.keyboards import room_detail_kb


logger = logging.getLogger(__name__)


router = Router(name="rooms")


def _parse_args(message: Message) -> list[str]:
    return (message.text or "").split()[1:]


@router.message(Command("create_room"))
async def create_room_cmd(message: Message, uow: UnitOfWork) -> None:
    args = _parse_args(message)
    if not args:
        await message.answer("Использование: /create_room <название>")
        return
    name = " ".join(args).strip()
    if not name:
        await message.answer("Нужно указать название комнаты.")
        return

    async def _delete_old_invite(user_id: int, message_id: int | None) -> None:
        if not message_id:
            return
        try:
            await message.bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception:
            pass

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]
        # Ensure user row exists before inserting Room with owner_id FK.
        await uow.session.flush()

        room_service = RoomService(RoomRepository(uow.session), RoomMemberRepository(uow.session))
        try:
            room_id = await room_service.create_room(
                name=name,
                owner_id=message.from_user.id,  # type: ignore[union-attr]
            )
        except DomainError as e:
            await message.answer(f"❌ {e}")
            return
        await uow.session.flush()

        # Get the created room to retrieve invite code
        room_repo = RoomRepository(uow.session)
        room = await room_repo.require(room_id)
        invite_code = room.invite_code
        room_name = room.name

        last_invite_message_id = None
        user = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
        if user:
            last_invite_message_id = user.last_invite_message_id

    await message.answer(
        room_created(room_id, room_name),
        parse_mode="Markdown",
        reply_markup=room_detail_kb(room_id, is_owner=True),
    )
    # Don't send invite automatically - user can request it via button
    logger.debug(f"create_room_cmd: Created room {room_id}, sent keyboard with is_owner=True")

@router.message(Command("join"))
async def join_room_cmd(message: Message, uow: UnitOfWork) -> None:
    args = _parse_args(message)
    if not args:
        await message.answer("Использование: /join <room_uuid>")
        return
    try:
        room_id = uuid.UUID(args[0])
    except ValueError:
        await message.answer("Некорректный ID комнаты.")
        return

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]

        room_service = RoomService(RoomRepository(uow.session), RoomMemberRepository(uow.session))
        try:
            await room_service.join_room(room_id=room_id, user_id=message.from_user.id)  # type: ignore[union-attr]
        except DomainError as e:
            await message.answer(f"❌ {e}")
            return

    await message.answer(
        joined_room(room_id),
        reply_markup=room_detail_kb(room_id, is_owner=False),
    )


@router.message(Command("join_invite"))
async def join_invite_cmd(message: Message, uow: UnitOfWork) -> None:
    args = _parse_args(message)
    if not args:
        await message.answer("Использование: /join_invite <код>")
        return
    invite_code = args[0].strip().upper()

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]

        room_service = RoomService(RoomRepository(uow.session), RoomMemberRepository(uow.session))
        try:
            room_id = await room_service.join_by_invite_code(
                invite_code=invite_code, user_id=message.from_user.id  # type: ignore[union-attr]
            )
        except DomainError as e:
            await message.answer(f"❌ {e}")
            return

    await message.answer(
        joined_room(room_id),
        reply_markup=room_detail_kb(room_id, is_owner=False),
    )

