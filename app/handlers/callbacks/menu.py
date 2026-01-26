from __future__ import annotations

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.domain.exceptions import DomainError
from app.repositories.rooms import RoomRepository
from app.repositories.uow import UnitOfWork
from app.repositories.users import UserRepository
from app.services.users import UserService
from app.ui.keyboards import MenuCb, RoomOpenCb, main_menu_kb, room_detail_kb, rooms_list_kb
from app.ui.messages import vacation_status, room_created, room_invite_share, help_message
from app.domain.enums.user import UserGlobalStatus


async def get_user_vacation_status(user_id: int, uow: UnitOfWork) -> str:
    """Get user's vacation status for menu display."""
    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        user = await user_repo.get(user_id)
        if user:
            return vacation_status(user.global_status)
    return vacation_status(UserGlobalStatus.ACTIVE)


router = Router(name="menu")


class MenuStates(StatesGroup):
    waiting_room_name = State()
    waiting_room_uuid = State()


@router.callback_query(MenuCb.filter())
async def menu_action(cb: CallbackQuery, callback_data: MenuCb, uow: UnitOfWork, state: FSMContext) -> None:
    action = callback_data.action
    
    # Get user's vacation status for menu display
    user_status = await get_user_vacation_status(cb.from_user.id, uow)  # type: ignore[union-attr]

    if action == "home":
        await state.clear()
        if cb.message:
            try:
                await cb.message.edit_text("Главное меню:", reply_markup=main_menu_kb(user_status))
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        if cb.message:
            async with uow:
                assert uow.session is not None
                user_repo = UserRepository(uow.session)
                user = await user_repo.get(cb.from_user.id)  # type: ignore[union-attr]
                if user:
                    user.last_menu_message_id = cb.message.message_id
                    await uow.session.flush()
        await cb.answer()
        return

    if action == "rooms":
        async with uow:
            assert uow.session is not None
            rooms = await RoomRepository(uow.session).list_rooms_for_user(user_id=cb.from_user.id)  # type: ignore[union-attr]
        if cb.message:
            try:
                if not rooms:
                    await cb.message.edit_text(
                        "У вас пока нет комнат. Создайте или вступите по коду/UUID.",
                        reply_markup=main_menu_kb(user_status),
                    )
                else:
                    await cb.message.edit_text(
                        "Ваши комнаты:",
                        reply_markup=rooms_list_kb([r.id for r in rooms], [r.name for r in rooms]),
                    )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        await cb.answer()
        return

    if action == "create_room":
        await state.set_state(MenuStates.waiting_room_name)
        if cb.message:
            try:
                await cb.message.edit_text("Введите название комнаты одним сообщением:")
                await state.update_data(room_name_prompt_id=cb.message.message_id)
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        await cb.answer()
        return

    if action == "join_room":
        await state.set_state(MenuStates.waiting_room_uuid)
        if cb.message:
            try:
                await cb.message.edit_text(
                    "Есть приглашение? Отправь код (или UUID, если его прислали) одним сообщением.\n\n"
                    "Если передумал(а) — выбери пункт в меню ниже.",
                    reply_markup=main_menu_kb(user_status),
                )
                await state.update_data(room_join_prompt_id=cb.message.message_id)
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        await cb.answer()
        return

    if action in ("vacation_on", "vacation_off", "vacation_toggle"):
        async with uow:
            assert uow.session is not None
            user_repo = UserRepository(uow.session)
            await UserService(user_repo).upsert_from_telegram(cb.from_user)  # type: ignore[arg-type]
            await uow.session.flush()
            # For toggle, determine current status and flip it
            if action == "vacation_toggle":
                user = await user_repo.get(cb.from_user.id)  # type: ignore[union-attr]
                from app.domain.enums.user import UserGlobalStatus
                enabled = user.global_status != UserGlobalStatus.VACATION if user else False
            else:
                enabled = (action == "vacation_on")
            try:
                await UserService(user_repo).set_vacation(cb.from_user.id, enabled=enabled)
            except DomainError as e:
                await cb.answer(f"❌ {e}", show_alert=True)
                return
        await cb.answer("Готово")
        if cb.message:
            # Reload status after change
            new_status = await get_user_vacation_status(cb.from_user.id, uow)  # type: ignore[union-attr]
            await cb.message.edit_text("Главное меню:", reply_markup=main_menu_kb(new_status))
        return

    if action == "help":
        if cb.message:
            try:
                await cb.message.edit_text(help_message(), parse_mode="Markdown", reply_markup=main_menu_kb(user_status))
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        await cb.answer()
        return

    await cb.answer("Неизвестное действие", show_alert=True)


@router.callback_query(RoomOpenCb.filter())
async def open_room(cb: CallbackQuery, callback_data: RoomOpenCb, uow: UnitOfWork) -> None:
    room_id = callback_data.room_id
    
    # Check if user is owner and if there's an open event
    is_owner = False
    open_event_id = None
    async with uow:
        assert uow.session is not None
        from app.repositories.rooms import RoomMemberRepository
        from app.domain.enums.room import RoomRole
        room_repo = RoomRepository(uow.session)
        room_members = RoomMemberRepository(uow.session)
        role = await room_members.get_role(room_id=room_id, user_id=cb.from_user.id)  # type: ignore[union-attr]
        is_owner = role == RoomRole.OWNER
        room = await room_repo.require(room_id)
        open_event_id = room.open_event_id
        room_name = room.name
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"open_room: room_id={room_id}, user_id={cb.from_user.id}, role={role}, is_owner={is_owner}, open_event_id={open_event_id}")

    if cb.message:
        await cb.message.edit_text(
            f"📍 Комната **{room_name}**\n\nМожно создать новое событие или вернуться к последнему.",
            parse_mode="Markdown",
            reply_markup=room_detail_kb(room_id, is_owner=is_owner, open_event_id=open_event_id),
        )
    await cb.answer()


@router.message(MenuStates.waiting_room_name)
async def create_room_from_text(message: Message, uow: UnitOfWork, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите ещё раз:")
        return

    async def _delete_prompt() -> None:
        data = await state.get_data()
        prompt_id = data.get("room_name_prompt_id")
        if prompt_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
            except Exception:
                pass
            await state.update_data(room_name_prompt_id=None)

    async def _delete_user_message() -> None:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception:
            pass

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
        await uow.session.flush()

        # Reuse existing service layer
        from app.repositories.rooms import RoomMemberRepository
        from app.services.rooms import RoomService

        room_id = await RoomService(RoomRepository(uow.session), RoomMemberRepository(uow.session)).create_room(
            name=name, owner_id=message.from_user.id  # type: ignore[union-attr]
        )

        await uow.session.flush()

        room_repo = RoomRepository(uow.session)
        room = await room_repo.require(room_id)
        invite_code = room.invite_code
        room_name = room.name

        last_invite_msg_id = None
        user = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
        if user:
            last_invite_msg_id = user.last_invite_message_id

    await state.clear()
    await _delete_user_message()
    await _delete_prompt()
    await message.answer(
        room_created(room_id, room_name),
        parse_mode="Markdown",
        reply_markup=room_detail_kb(room_id, is_owner=True),
    )

    await _delete_old_invite(message.from_user.id, last_invite_msg_id)  # type: ignore[arg-type]

    invite_msg = await message.answer(
        room_invite_share(room_id, room_name, invite_code),
        parse_mode="Markdown",
    )

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        user = await user_repo.get(message.from_user.id)  # type: ignore[union-attr]
        if user:
            user.last_invite_message_id = invite_msg.message_id
            await uow.session.flush()


@router.message(MenuStates.waiting_room_uuid)
async def join_room_from_text(message: Message, uow: UnitOfWork, state: FSMContext) -> None:
    import uuid

    raw = (message.text or "").strip().strip("`")
    try:
        room_id = uuid.UUID(raw)
    except ValueError:
        user_status_text = await get_user_vacation_status(message.from_user.id, uow)  # type: ignore[union-attr]
        await message.answer(
            "Не похоже на код приглашения или UUID. Отправь код ещё раз или выбери пункт в меню ниже.",
            reply_markup=main_menu_kb(user_status_text),
        )
        return

    async def _delete_prompt() -> None:
        data = await state.get_data()
        prompt_id = data.get("room_join_prompt_id")
        if prompt_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
            except Exception:
                pass
            await state.update_data(room_join_prompt_id=None)

    async with uow:
        assert uow.session is not None
        user_repo = UserRepository(uow.session)
        await UserService(user_repo).upsert_from_telegram(message.from_user)  # type: ignore[arg-type]
        await uow.session.flush()

        from app.repositories.rooms import RoomMemberRepository
        from app.services.rooms import RoomService

        try:
            await RoomService(RoomRepository(uow.session), RoomMemberRepository(uow.session)).join_room(
                room_id=room_id, user_id=message.from_user.id  # type: ignore[union-attr]
            )
        except DomainError as e:
            user_status_text = await get_user_vacation_status(message.from_user.id, uow)  # type: ignore[union-attr]
            await message.answer(f"❌ {e}\n\nПопробуйте ещё раз UUID или вернитесь в меню.", reply_markup=main_menu_kb(user_status_text))
            await state.clear()
            await _delete_prompt()
            return

    await state.clear()
    await _delete_prompt()
    await message.answer("✅ Вступили в комнату.", reply_markup=room_detail_kb(room_id, is_owner=False))

