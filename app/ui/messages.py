from __future__ import annotations

import uuid

from app.domain.enums.event import ParticipationState, EventType
from app.domain.enums.user import UserGlobalStatus


def room_created(room_id: uuid.UUID) -> str:
    return (
        "✅ Room created.\n\n"
        f"Room id: `{room_id}`\n"
        "Invite colleagues by sending them:\n"
        f"`/join {room_id}`"
    )


def joined_room(room_id: uuid.UUID) -> str:
    return f"✅ Joined room `{room_id}`"


def event_created(event_id: uuid.UUID) -> str:
    return f"🚬 Event created: `{event_id}`"


def participation_label(state: ParticipationState) -> str:
    return {
        ParticipationState.PENDING: "⏳ Pending",
        ParticipationState.ACCEPTED: "✅ Accepted",
        ParticipationState.LATER: "🕒 Later",
        ParticipationState.DECLINED: "❌ Declined",
        ParticipationState.VACATION: "🌴 Vacation",
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
    return f"✅ Событие '{event_type_display(event_type)}' создано!\n\nID: `{event_id}`"


def event_notification_with_statuses(room_name: str, event_type: EventType, event_id: uuid.UUID) -> str:
    """Format notification about new event."""
    return f"📣 В комнате '{room_name}' создано событие {event_type_display(event_type)}\n\nID: `{event_id}`"


def confirm_delete_room(room_id: uuid.UUID) -> str:
    return f"⚠️ Are you sure you want to delete room `{room_id}`? This action cannot be undone."


def room_deleted() -> str:
    return "✅ Room has been deleted."

