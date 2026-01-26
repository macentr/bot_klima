from __future__ import annotations

import uuid

from app.domain.enums.event import ParticipationState, EventType
from app.domain.enums.user import UserGlobalStatus


def room_created(room_id: uuid.UUID, room_name: str) -> str:
    return f"✅ Комната **{room_name}** создана!\n\nВаше приглашение для коллег придёт следующим сообщением — просто перешлите его."


def joined_room(room_id: uuid.UUID) -> str:
    return "✅ Вы успешно вступили в комнату!"


def event_created(event_id: uuid.UUID) -> str:
    return "📌 Событие создано!"


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
        f"👋 Привет, коллега! Рад видеть тебя в боте **«Возьмите Клима»**!\n\n"
        f"Знаю, что никто не любит пропускать курилку или случайно пить кофе в одиночку. "
        f"Поэтому я здесь — чтобы синхронизировать офлайн-события и собрать всех вместе! 😎\n\n"
        f"🎯 **Что умею:**\n"
        f"• Создавать комнаты для команды\n"
        f"• Организовывать события (🚬 курилка, ☕ кофе, 🚶 прогулка)\n"
        f"• Собирать отклики коллег в реальном времени\n"
        f"• Управлять статусом отпуска\n\n"
        f"📊 Ваш статус: {vacation_status}\n\n"
        f"💡 Не знаешь с чего начать? Набери /help для краткого гайда.\n\n"
        f"А теперь давай перейдём к делу — выбирай действие! 👇"
    )


def event_created_with_statuses(event_type: EventType, event_id: uuid.UUID) -> str:
    """Format event creation message with type name."""
    return f"✅ Событие «{event_type_display(event_type)}» создано!"


def event_notification_with_statuses(room_name: str, event_type: EventType, event_id: uuid.UUID) -> str:
    """Format notification about new event."""
    return f"📣 В комнате «{room_name}» создано событие {event_type_display(event_type)}"


def confirm_delete_room(room_id: uuid.UUID) -> str:
    return "⚠️ Удалить комнату? Действие необратимо."


def room_deleted() -> str:
    return "✅ Комната удалена."


def help_message() -> str:
    """Quick start guide for new users."""
    return (
        "📖 **Как пользоваться ботом**\n\n"
        "**🎯 Зачем это нужно?**\n"
        "• Синхронизируй перерывы с коллегами\n"
        "• Не пропускай курилку или кофе-брейк\n"
        "• Мгновенные уведомления в реальном времени\n"
        "• Видишь, кто идёт, кто ещё думает\n\n"
        "**📱 Сценарий 1: Вступить в комнату по приглашению**\n"
        "1. Коллега прислал тебе код (например, `A1B2C3D4`)\n"
        "2. Нажми **\"🔗 Есть приглашение? Войти\"** в меню\n"
        "3. Отправь код одним сообщением\n"
        "4. Готово! Теперь ты будешь получать уведомления о событиях\n\n"
        "**🏠 Сценарий 2: Создать свою комнату**\n"
        "1. Нажми **\"➕ Создать комнату\"** в меню\n"
        "2. Введи название (например, \"Отдел маркетинга\")\n"
        "3. Получишь приглашение — перешли коллегам\n"
        "4. Запускай события кнопками: **🚬 Курилка**, **☕ Кофе**, **🚶 Прогулка**\n\n"
        "**💬 Как работают события?**\n"
        "• Создатель сразу видит, кто откликнулся\n"
        "• Участники выбирают: **✅ Пойду** • **🕒 Позже** • **❌ Не смогу**\n"
        "• Все видят актуальный список в реальном времени\n\n"
        "**⚙️ Дополнительная информация**\n"
        "⏱ **Тайминги:** События длятся 5 минут. Новое можно создать только через 5 минут после закрытия предыдущего.\n\n"
        "🌴 **Режим отпуска:** Нажми кнопку **\"Отпуск\"** в меню, чтобы не получать уведомления. Вернувшись, просто выключи его — останешься в комнатах.\n\n"
        "📍 **Кнопка \"Приглашение\"** (только для владельца): Получи свежее сообщение с кодом, чтобы переслать новым коллегам.\n\n"
        "💡 **Совет:** Используй **\"🔄 Вернуться к последнему событию\"**, если случайно закрыл уведомление."
    )


def room_invite_share(room_id: uuid.UUID, room_name: str, invite_code: str | None) -> str:
    bot_link = "https://t.me/perevent_bot"
    bot_link_display = "t.me/perevent_bot"
    if invite_code:
        return (
            f"📩 **Приглашение в комнату \"{room_name}\"**\n\n"
            "🔹 Перешлите это сообщение коллегам\n\n"
            f"1️⃣ Откройте бота: [{bot_link_display}]({bot_link})\n"
            f"2️⃣ Используйте команду:\n"
            f"`/join_invite {invite_code}`\n\n"
            f"💡 Или отправьте код `{invite_code}` в меню бота"
        )
    return (
        f"📩 **Приглашение в комнату \"{room_name}\"**\n\n"
        "🔹 Свяжитесь с владельцем комнаты для получения кода приглашения\n\n"
        f"Откройте бота: [{bot_link_display}]({bot_link})"
    )

