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
    kb.button(text="✅ ACCEPT", callback_data=EventActionCb(event_id=event_id, action="accept").pack())
    kb.button(text="🕒 LATER", callback_data=EventActionCb(event_id=event_id, action="later").pack())
    kb.button(text="❌ DECLINE", callback_data=EventActionCb(event_id=event_id, action="decline").pack())
    if include_refresh:
        kb.button(text="🔄 Refresh", callback_data=EventActionCb(event_id=event_id, action="refresh").pack())
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
        ("🚬 SMOKE", EventType.SMOKE),
        ("☕ COFFEE", EventType.COFFEE),
        ("🚶 WALK", EventType.WALK),
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
    kb.button(text="🔗 Вступить по UUID", callback_data=MenuCb(action="join_room").pack())
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


def room_detail_kb(room_id: uuid.UUID, is_owner: bool = False) -> InlineKeyboardMarkup:
    # Reuse event creation buttons + back to rooms
    logger.debug(f"room_detail_kb called with room_id={room_id}, is_owner={is_owner}")
    kb = InlineKeyboardBuilder()
    for text, etype in [
        ("🚬 SMOKE (5m)", EventType.SMOKE),
        ("☕ COFFEE (5m)", EventType.COFFEE),
        ("🚶 WALK (5m)", EventType.WALK),
    ]:
        kb.button(text=text, callback_data=RoomEventCreateCb(room_id=room_id, event_type=etype.value).pack())
    if is_owner:
        logger.debug(f"Adding delete button for owner")
        kb.button(text="🗑️ Delete Room", callback_data=RoomDeleteCb(room_id=room_id).pack())
    else:
        logger.debug(f"Not adding delete button - not owner")
    kb.button(text="⬅️ К списку комнат", callback_data=MenuCb(action="rooms").pack())
    kb.adjust(1)
    return kb.as_markup()


def confirm_delete_room_kb(room_id: uuid.UUID) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Delete", callback_data=ConfirmDeleteRoomCb(room_id=room_id, confirmed=True).pack())
    kb.button(text="❌ Cancel", callback_data=ConfirmDeleteRoomCb(room_id=room_id, confirmed=False).pack())
    kb.adjust(2)
    return kb.as_markup()


def event_notification_kb(event_id: uuid.UUID) -> InlineKeyboardMarkup:
    """Keyboard for event notifications with menu button always visible."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ ACCEPT", callback_data=EventActionCb(event_id=event_id, action="accept").pack())
    kb.button(text="🕒 LATER", callback_data=EventActionCb(event_id=event_id, action="later").pack())
    kb.button(text="❌ DECLINE", callback_data=EventActionCb(event_id=event_id, action="decline").pack())
    kb.button(text="⬅️ Меню", callback_data=MenuCb(action="home").pack())
    kb.adjust(2)
    return kb.as_markup()

