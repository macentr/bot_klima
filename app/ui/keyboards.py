from __future__ import annotations

import uuid
import logging

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.domain.enums.event import ParticipationState
from app.domain.enums.event import EventType


logger = logging.getLogger(__name__)


class EventActionCb(CallbackData, prefix="evt"):
    event_id: uuid.UUID
    action: str  # accept|later|decline|refresh


class RoomEventCreateCb(CallbackData, prefix="room_evt"):
    room_id: uuid.UUID
    event_type: str  # SMOKE|COFFEE|WALK


class MenuCb(CallbackData, prefix="menu"):
    action: str  # home|rooms|create_room|join_room|vacation_on|vacation_off


class RoomOpenCb(CallbackData, prefix="room"):
    room_id: uuid.UUID


class RoomDeleteCb(CallbackData, prefix="room_del"):
    room_id: uuid.UUID


class ConfirmDeleteRoomCb(CallbackData, prefix="confirm_del_room"):
    room_id: uuid.UUID
    confirmed: bool


def event_actions_kb(event_id: uuid.UUID, *, include_refresh: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Пойду", callback_data=EventActionCb(event_id=event_id, action="accept").pack())
    kb.button(text="🕒 Позже", callback_data=EventActionCb(event_id=event_id, action="later").pack())
    kb.button(text="❌ Не смогу", callback_data=EventActionCb(event_id=event_id, action="decline").pack())
    if include_refresh:
        kb.button(text="🔄 Обновить", callback_data=EventActionCb(event_id=event_id, action="refresh").pack())
    kb.adjust(1)
    return kb.as_markup()


def map_action_to_state(action: str) -> ParticipationState | None:
    return {
        "accept": ParticipationState.ACCEPTED,
        "later": ParticipationState.LATER,
        "decline": ParticipationState.DECLINED,
        "refresh": None,
    }[action]


def room_event_create_kb(room_id: uuid.UUID) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for text, etype in [
        ("🚬 Курилка (5 мин)", EventType.SMOKE),
        ("☕ Кофе (5 мин)", EventType.COFFEE),
        ("🚶 Прогулка (5 мин)", EventType.WALK),
    ]:
        kb.button(
            text=text,
            callback_data=RoomEventCreateCb(room_id=room_id, event_type=etype.value).pack(),
        )
    kb.adjust(1)
    return kb.as_markup()


def main_menu_kb(vacation_status: str = "💼 На работе") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Мои комнаты", callback_data=MenuCb(action="rooms").pack())
    kb.button(text="➕ Создать комнату", callback_data=MenuCb(action="create_room").pack())
    kb.button(text="🔗 Есть приглашение? Войти", callback_data=MenuCb(action="join_room").pack())
    kb.button(text=f"Отпуск: {vacation_status}", callback_data=MenuCb(action="vacation_toggle").pack())
    kb.adjust(1)
    return kb.as_markup()


def rooms_list_kb(room_ids: list[uuid.UUID], room_titles: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for rid, title in zip(room_ids, room_titles, strict=True):
        kb.button(text=f"🏠 {title}", callback_data=RoomOpenCb(room_id=rid).pack())
    kb.button(text="⬅️ Назад", callback_data=MenuCb(action="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def room_detail_kb(room_id: uuid.UUID, is_owner: bool = False, open_event_id: uuid.UUID | None = None) -> InlineKeyboardMarkup:
    # Reuse event creation buttons + back to rooms
    logger.debug(f"room_detail_kb called with room_id={room_id}, is_owner={is_owner}, open_event_id={open_event_id}")
    kb = InlineKeyboardBuilder()

    # Creation buttons always visible
    for text, etype in [
        ("🚬 Курилка (5 мин)", EventType.SMOKE),
        ("☕ Кофе (5 мин)", EventType.COFFEE),
        ("🚶 Прогулка (5 мин)", EventType.WALK),
    ]:
        kb.button(text=text, callback_data=RoomEventCreateCb(room_id=room_id, event_type=etype.value).pack())

    # If there's a previous event, allow returning to it
    if open_event_id:
        kb.button(text="🔄 Вернуться к последнему событию", callback_data=EventActionCb(event_id=open_event_id, action="refresh").pack())
    
    if is_owner:
        logger.debug("Adding delete button for owner")
        kb.button(text="🗑️ Удалить комнату", callback_data=RoomDeleteCb(room_id=room_id).pack())
    else:
        logger.debug("Not adding delete button - not owner")
    kb.button(text="⬅️ К списку комнат", callback_data=MenuCb(action="rooms").pack())
    kb.adjust(1)
    return kb.as_markup()


def confirm_delete_room_kb(room_id: uuid.UUID) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Удалить", callback_data=ConfirmDeleteRoomCb(room_id=room_id, confirmed=True).pack())
    kb.button(text="❌ Отмена", callback_data=ConfirmDeleteRoomCb(room_id=room_id, confirmed=False).pack())
    kb.adjust(2)
    return kb.as_markup()


def event_notification_kb(event_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Keyboard for event notifications with menu button always visible."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Пойду", callback_data=EventActionCb(event_id=event_id, action="accept").pack())
    kb.button(text="🕒 Позже", callback_data=EventActionCb(event_id=event_id, action="later").pack())
    kb.button(text="❌ Не смогу", callback_data=EventActionCb(event_id=event_id, action="decline").pack())
    kb.button(text="⬅️ Меню", callback_data=MenuCb(action="home").pack())
    kb.adjust(2)
    return kb.as_markup()


def invite_copy_kb(invite_code: str | None, room_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Inline buttons that prefill join commands in the input field for quick copying."""
    kb = InlineKeyboardBuilder()
    if invite_code:
        kb.button(
            text="📋 Скопировать /join_invite",
            switch_inline_query_current_chat=f"/join_invite {invite_code}",
        )
    kb.button(
        text="📋 Скопировать /join",
        switch_inline_query_current_chat=f"/join {room_id}",
    )
    kb.adjust(1)
    return kb.as_markup()

