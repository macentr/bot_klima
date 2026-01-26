from __future__ import annotations

import uuid

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

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
from app.ui.keyboards import (
    RoomEventCreateCb,
    RoomDeleteCb,
    ConfirmDeleteRoomCb,
    RoomInviteCb,
    event_actions_kb,
    room_detail_kb,
    confirm_delete_room_kb,
    event_notification_kb,
)
from app.ui.messages import confirm_delete_room, room_deleted, event_created_with_statuses, event_notification_with_statuses, participation_label, room_invite_share
from app.services.rooms import RoomService


router = Router(name="room_callbacks")


async def _delete_message_safe(bot: Bot, chat_id: int, message_id: int | None) -> None:
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


@router.callback_query(RoomEventCreateCb.filter())
async def room_create_event_from_button(
    cb: CallbackQuery,
    callback_data: RoomEventCreateCb,
    bot: Bot,
    uow: UnitOfWork,
) -> None:
    room_id: uuid.UUID = callback_data.room_id
    event_type = EventType(callback_data.event_type)

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(cb.from_user)  # type: ignore[arg-type]
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
                creator_id=cb.from_user.id,  # type: ignore[union-attr]
                event_type=event_type,
                auto_close_minutes=5,
            )
        except DomainError as e:
            await cb.answer(f"❌ {e}", show_alert=True)
            return

        # Get room name
        room = await room_repo.require(room_id)
        
        # Get all members with their participation status for this event
        participation_repo = ParticipationRepository(uow.session)
        participants_with_users = await participation_repo.list_with_users(event_id)
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Event {event_id} created. Found {len(participants_with_users)} participants")
        for p, u in participants_with_users:
            logger.debug(f"  Participant: {u.id} ({u.display_name}) - state: {p.state}")
        
        # Build member list with statuses
        member_list = []
        recipients: list[int] = []

        for participation, user in participants_with_users:
            display_name = user.display_name or f"Пользователь {user.id}"
            member_list.append(f"{display_name}: {participation_label(participation.state)}")

            # Add to recipients if active, not creator, and not in vacation
            if participation.user_id != cb.from_user.id and user.global_status == UserGlobalStatus.ACTIVE:  # type: ignore[union-attr]
                recipients.append(participation.user_id)

    # Send notification to other members with event info and member statuses
    notif = NotificationService(bot)
    member_statuses_text = "\n".join(member_list) if member_list else "Нет участников"
    event_message = event_notification_with_statuses(room.name, event_type, event_id)
    full_message = f"{event_message}\n\nУчастники:\n{member_statuses_text}"
    
    await notif.send_many(
        recipients,
        text=full_message,
        reply_markup=event_notification_kb(event_id, room_id),
    )
    
    if cb.message:
        creator_message = f"{event_created_with_statuses(event_type, event_id)}\n\nУчастники:\n{member_statuses_text}"
        creator_msg = await cb.message.answer(creator_message, parse_mode="Markdown", reply_markup=event_notification_kb(event_id, room_id))
        
        # Save creator_message_id and open_event_id in event for later updates
        async with uow:
            assert uow.session is not None
            event_repo = EventRepository(uow.session)
            event = await event_repo.get(event_id)
            if event:
                event.creator_message_id = creator_msg.message_id
                await uow.session.flush()
            
            # Save open_event_id in room and delete old menu message
            room_repo = RoomRepository(uow.session)
            room = await room_repo.require(room_id)
            room.open_event_id = event_id
            await uow.session.flush()
        
        # Delete the old room menu message if it exists
        try:
            if cb.message:
                await cb.message.delete()
        except Exception:
            pass
    await cb.answer("Готово")


@router.callback_query(RoomDeleteCb.filter())
async def delete_room_prompt(cb: CallbackQuery, callback_data: RoomDeleteCb, uow: UnitOfWork) -> None:
    """Show confirmation dialog for room deletion."""
    room_id = callback_data.room_id

    async with uow:
        assert uow.session is not None
        room_members = RoomMemberRepository(uow.session)
        role = await room_members.get_role(room_id=room_id, user_id=cb.from_user.id)  # type: ignore[union-attr]
        if role is None:
            await cb.answer("❌ Вы не участник этой комнаты", show_alert=True)
            return
        from app.domain.enums.room import RoomRole
        if role != RoomRole.OWNER:
            await cb.answer("❌ Только владелец может удалить комнату", show_alert=True)
            return

    if cb.message:
        try:
            await cb.message.edit_text(
                confirm_delete_room(room_id),
                parse_mode="Markdown",
                reply_markup=confirm_delete_room_kb(room_id),
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
    await cb.answer()


@router.callback_query(RoomInviteCb.filter())
async def send_room_invite(cb: CallbackQuery, callback_data: RoomInviteCb, uow: UnitOfWork, bot: Bot) -> None:
    """Send invite message to the requester and replace previous invite message."""
    room_id = callback_data.room_id

    async with uow:
        assert uow.session is not None
        room_repo = RoomRepository(uow.session)
        room_members = RoomMemberRepository(uow.session)
        room = await room_repo.require(room_id)
        invite_code = room.invite_code
        role = await room_members.get_role(room_id=room_id, user_id=cb.from_user.id)  # type: ignore[union-attr]
        from app.domain.enums.room import RoomRole
        if role != RoomRole.OWNER:
            await cb.answer("❌ Только владелец может отправлять приглашение", show_alert=True)
            return

        user_repo = UserRepository(uow.session)
        user = await user_repo.get(cb.from_user.id)  # type: ignore[union-attr]
        last_invite_message_id = user.last_invite_message_id if user else None

    await _delete_message_safe(bot, cb.from_user.id, last_invite_message_id)  # type: ignore[arg-type]

    text = room_invite_share(room_id, room.name, invite_code)
    invite_msg = await bot.send_message(
        chat_id=cb.from_user.id,
        text=text,
        parse_mode="Markdown",
    )

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        user = await user_repo.get(cb.from_user.id)  # type: ignore[union-attr]
        if user:
            user.last_invite_message_id = invite_msg.message_id
            await uow.session.flush()

    await cb.answer("Приглашение отправлено")


@router.callback_query(ConfirmDeleteRoomCb.filter())
async def confirm_delete_room_action(cb: CallbackQuery, callback_data: ConfirmDeleteRoomCb, uow: UnitOfWork) -> None:
    """Handle room deletion confirmation."""
    room_id = callback_data.room_id
    confirmed = callback_data.confirmed

    if not confirmed:
        if cb.message:
            async with uow:
                assert uow.session is not None
                room = await RoomRepository(uow.session).require(room_id)
            await cb.message.edit_text(
                f"📍 Комната **{room.name}**\n\nВыберите событие для создания:",
                parse_mode="Markdown",
                reply_markup=room_detail_kb(room_id, is_owner=True),
            )
        await cb.answer("Удаление отменено")
        return

    async with uow:
        assert uow.session is not None
        room_repo = RoomRepository(uow.session)
        room_members = RoomMemberRepository(uow.session)
        room_service = RoomService(room_repo, room_members)

        try:
            await room_service.delete_room(
                room_id=room_id,
                user_id=cb.from_user.id,  # type: ignore[union-attr]
            )
        except DomainError as e:
            await cb.answer(f"❌ {e}", show_alert=True)
            return

    if cb.message:
        from app.ui.keyboards import main_menu_kb
        from app.ui.messages import vacation_status
        from app.repositories.users import UserRepository
        from app.domain.enums.user import UserGlobalStatus
        
        # Get user's current status
        user_status_text = UserGlobalStatus.ACTIVE
        async with uow:
            assert uow.session is not None
            user = await UserRepository(uow.session).get(cb.from_user.id)  # type: ignore[union-attr]
            if user:
                user_status_text = user.global_status
        
        await cb.message.edit_text(
            room_deleted(),
            reply_markup=main_menu_kb(vacation_status(user_status_text)),
        )
    await cb.answer("✅ Комната удалена")

