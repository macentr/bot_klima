from __future__ import annotations

import uuid

from app.domain.enums.event import ParticipationState, EventType
from app.domain.enums.user import UserGlobalStatus


def room_created(room_id: uuid.UUID, room_name: str) -> str:
    return f"✅ Комната **{room_name}** создана!\n\nВаше приглашение для коллег придёт следующим сообщением — просто перешлите его."


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
    return (
        f"👋 Привет! Это бот **«Возьмите Клима»** — твой помощник для синхронизации коротких офлайн событий с коллегами.\n\n"
        f"🎯 **Что умеет бот:**\n"
        f"• Создавать комнаты для команды\n"
        f"• Организовывать события (курилка, кофе, прогулка)\n"
        f"• Собирать отклики коллег в реальном времени\n"
        f"• Управлять статусом отпуска\n\n"
        f"📊 Ваш статус: {vacation_status}\n\n"
        f"Используйте /help для краткого гайда.\n\n"
        f"Выберите действие:"
    )


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


def help_message() -> str:
    """Quick start guide for new users."""
    return (
        "📖 **Краткий гайд по боту**\n\n"
        "**1️⃣ Создайте комнату**\n"
        "Нажмите \"➕ Создать комнату\" или используйте команду:\n"
        "/create_room Название\n\n"
        "**2️⃣ Пригласите коллег**\n"
        "После создания комнаты вам придёт сообщение с инвайт-кодом — перешлите его коллегам. Они смогут подключиться командой:\n"
        "/join_invite КОД\n\n"
        "**3️⃣ Создайте событие**\n"
        "Откройте комнату и нажмите на тип события (🚬 Курилка, ☕ Кофе, 🚶 Прогулка). Все участники комнаты получат уведомление.\n\n"
        "**4️⃣ Отвечайте на события**\n"
        "Получив уведомление, выберите:\n"
        "• ✅ Пойду — принять участие\n"
        "• 🕒 Позже — присоединюсь позднее\n"
        "• ❌ Не смогу — отказаться\n\n"
        "**⚙️ Дополнительные команды:**\n"
        "/vacation_on — включить режим отпуска\n"
        "/vacation_off — выключить режим отпуска\n"
        "/menu — вернуться в главное меню\n\n"
        "💡 **Совет:** события автоматически закрываются через 5 минут. Между созданием событий должен пройти минимум 5 минут."
    )


def room_invite_share(bot_username: str, room_id: uuid.UUID, room_name: str, invite_code: str | None) -> str:
    bot_link = f"https://t.me/{bot_username}" if bot_username else "бот"
    if invite_code:
        return (
            f"📩 **Приглашение в комнату \"{room_name}\"**\n\n"
            "🔹 Перешлите это сообщение коллегам\n\n"
            f"1️⃣ Откройте бота: {bot_link}\n"
            f"2️⃣ Нажмите на кнопку, чтобы вставить команду:\n"
            f"/join_invite {invite_code}\n\n"
            f"💡 Альтернатива — отправьте код `{invite_code}` в меню бота\n\n"
            f"⚙️ Резервный вариант (UUID):\n"
            f"/join {room_id}"
        )
    return (
        f"📩 **Приглашение в комнату \"{room_name}\"**\n\n"
        "🔹 Перешлите это сообщение коллегам\n\n"
        f"1️⃣ Откройте бота: {bot_link}\n"
        f"2️⃣ Нажмите на кнопку, чтобы вставить команду:\n"
        f"/join {room_id}"
    )

