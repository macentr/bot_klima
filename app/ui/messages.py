from __future__ import annotations

import uuid

from app.domain.enums.event import ParticipationState, EventType
from app.domain.enums.user import UserGlobalStatus


def room_created(room_id: uuid.UUID, invite_code: str | None = None) -> str:
    msg = "✅ Комната создана.\n\n"
    if invite_code:
        msg += (
            f"Пригласительный код: `{invite_code}`\n\n"
            "Коллеги могут вступить командой:\n"
            f"`/join_invite {invite_code}`\n\n"
            "Или отправив код в меню."
        )
    else:
        msg += (
            f"ID комнаты: `{room_id}`\n"
            "Пригласите коллег командой:\n"
            f"`/join {room_id}`"
        )
    return msg


def joined_room(room_id: uuid.UUID) -> str:
    return f"✅ Вы вступили в комнату `{room_id}`"


def event_created(event_id: uuid.UUID) -> str:
    return f"📌 Событие создано: `{event_id}`"


def participation_label(state: ParticipationState) -> str:
    return {
        ParticipationState.PENDING: "⏳ Ожидает",
        ParticipationState.ACCEPTED: "✅ Пойду",
        ParticipationState.LATER: "🕒 Позже",
        ParticipationState.DECLINED: "❌ Не смогу",
        ParticipationState.VACATION: "🌴 В отпуске",
    }[state]


def event_type_display(event_type: EventType) -> str:
    """Get user-friendly name for event type."""
    return {
        EventType.SMOKE: "🚬 Курение",
        EventType.COFFEE: "☕ Кофе",
        EventType.WALK: "🚶 Прогулка",
        EventType.CUSTOM: "📌 Событие",
    }[event_type]


def vacation_status(status: UserGlobalStatus) -> str:
    """Get vacation status display."""
    return "🌴 В отпуске" if status == UserGlobalStatus.VACATION else "💼 На работе"


def main_menu_greeting(vacation_status: str) -> str:
    """Format main menu greeting with vacation status."""
    return f"Привет! Это бот «Возьмите Клима».\n\nВаш статус: {vacation_status}\n\nВыберите действие:"


def event_created_with_statuses(event_type: EventType, event_id: uuid.UUID) -> str:
    """Format event creation message with type name."""
    return f"✅ Событие «{event_type_display(event_type)}» создано!\n\nID: `{event_id}`"


def event_notification_with_statuses(room_name: str, event_type: EventType, event_id: uuid.UUID) -> str:
    """Format notification about new event."""
    return f"📣 В комнате «{room_name}» создано событие {event_type_display(event_type)}\n\nID: `{event_id}`"


def confirm_delete_room(room_id: uuid.UUID) -> str:
    return f"⚠️ Удалить комнату `{room_id}`? Действие необратимо."


def room_deleted() -> str:
    return "✅ Комната удалена."


def room_invite_share(bot_username: str, room_id: uuid.UUID, invite_code: str | None) -> str:
    bot_link = f"https://t.me/{bot_username}" if bot_username else "бот"
    if invite_code:
        return (
            "Перешлите это сообщение коллегам, чтобы подключить их к боту и комнате.\n\n"
            f"1) Откройте бота: {bot_link}\n"
            f"2) Введите команду: /join_invite {invite_code}\n"
            "   или отправьте код в меню.\n\n"
            "Если не сработало, можно использовать UUID комнаты:\n"
            f"/join {room_id}"
        )
    return (
        "Перешлите это сообщение коллегам, чтобы подключить их к боту и комнате.\n\n"
        f"1) Откройте бота: {bot_link}\n"
        f"2) Введите команду: /join {room_id}"
    )

