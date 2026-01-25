from __future__ import annotations

import uuid

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.domain.enums.event import EventType
from app.domain.enums.user import UserGlobalStatus
from app.domain.exceptions import DomainError
from app.repositories.events import EventRepository, ParticipationRepository
from app.repositories.rooms import RoomMemberRepository, RoomRepository
from app.repositories.uow import UnitOfWork
from app.repositories.users import UserRepository
from app.services.access import AccessControl
from app.services.events import EventService
from app.services.notifications import NotificationService
from app.services.users import UserService
from app.ui.keyboards import event_actions_kb


router = Router(name="events")


def _parse_args(message: Message) -> list[str]:
    return (message.text or "").split()[1:]


@router.message(Command("event"))
async def create_event_cmd(message: Message, bot: Bot, uow: UnitOfWork) -> None:
    args = _parse_args(message)
    if len(args) < 2:
        await message.answer("Использование: /event <room_uuid> <SMOKE|COFFEE|WALK|CUSTOM> [auto_close_minutes]")
        return

    try:
        room_id = uuid.UUID(args[0])
    except ValueError:
        await message.answer("Некорректный ID комнаты.")
        return

    try:
        event_type = EventType(args[1].upper())
    except ValueError:
        await message.answer("Некорректный тип события.")
        return

    auto_close_minutes: int | None = None
    if len(args) >= 3:
        try:
            auto_close_minutes = int(args[2])
        except ValueError:
            await message.answer("auto_close_minutes должен быть числом.")
            return

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]
        # Ensure creator row exists before inserting Event with creator_id FK.
        await uow.session.flush()

        room_repo = RoomRepository(uow.session)
        room_members = RoomMemberRepository(uow.session)
        access = AccessControl(room_members)
        service = EventService(
            events=EventRepository(uow.session),
            participations=ParticipationRepository(uow.session),
            rooms=room_repo,
            room_members=room_members,
            users=user_repo,
            access=access,
        )

        try:
            event_id = await service.create_event(
                room_id=room_id,
                creator_id=message.from_user.id,  # type: ignore[union-attr]
                event_type=event_type,
                auto_close_minutes=auto_close_minutes,
            )
        except DomainError as e:
            await message.answer(f"❌ {e}")
            return

        # Notify ACTIVE members only (excluding creator). No spam on responses.
        member_ids = await room_members.list_member_ids(room_id=room_id)
        recipients: list[int] = []
        for uid in member_ids:
            if uid == message.from_user.id:  # type: ignore[union-attr]
                continue
            u = await user_repo.get(uid)
            if u is None:
                continue
            if u.global_status != UserGlobalStatus.ACTIVE:
                continue
            recipients.append(uid)

    # Get room name for notification
    room = await room_repo.require(room_id)
    notif = NotificationService(bot)
    await notif.send_many(
        recipients,
        text=f"📣 Новое событие в комнате **{room.name}**",
        reply_markup=event_actions_kb(event_id),
    )
    await message.answer("✅ Событие создано!", parse_mode="Markdown")

