from __future__ import annotations

import uuid

from aiogram import Bot, Router
from aiogram.types import CallbackQuery

from app.domain.enums.event import ParticipationState
from app.domain.exceptions import DomainError
from app.repositories.events import EventRepository, ParticipationRepository
from app.repositories.uow import UnitOfWork
from app.ui.keyboards import EventActionCb, map_action_to_state


router = Router(name="event_callbacks")


@router.callback_query(EventActionCb.filter())
async def event_action(cb: CallbackQuery, callback_data: EventActionCb, uow: UnitOfWork, bot: Bot) -> None:
    event_id: uuid.UUID = callback_data.event_id
    action = callback_data.action
    new_state = map_action_to_state(action)

    async with uow:
        assert uow.session is not None
        events = EventRepository(uow.session)
        participations = ParticipationRepository(uow.session)
        try:
            # Ensure event exists.
            event = await events.require(event_id)
            if new_state is not None:
                await participations.set_state_idempotent(
                    event_id=event_id,
                    user_id=cb.from_user.id,
                    new_state=new_state,
                )
        except DomainError as e:
            await cb.answer(f"❌ {e}", show_alert=True)
            return

        rows = await participations.list_with_users(event_id)

    # Render summary: counts + поимённый список c эмодзи.
    counts: dict[ParticipationState, int] = {s: 0 for s in ParticipationState}
    lines: list[str] = []
    for part, user in rows:
        counts[part.state] += 1
        prefix = {
            ParticipationState.ACCEPTED: "✅",
            ParticipationState.LATER: "🕒",
            ParticipationState.DECLINED: "❌",
            ParticipationState.PENDING: "⏳",
            ParticipationState.VACATION: "🌴",
        }[part.state]
        lines.append(f"{prefix} {user.display_name}")

    text = (
        f"Event `{event_id}`\n\n"
        f"✅ Accepted: {counts[ParticipationState.ACCEPTED]}\n"
        f"🕒 Later: {counts[ParticipationState.LATER]}\n"
        f"❌ Declined: {counts[ParticipationState.DECLINED]}\n"
        f"⏳ Pending: {counts[ParticipationState.PENDING]}\n"
        f"🌴 Vacation: {counts[ParticipationState.VACATION]}\n\n"
        + "\n".join(lines)
    )

    # After a response, buttons should disappear (except Refresh is still useful).
    # For MVP: if action was refresh, keep buttons; else remove keyboard.
    if cb.message:
        if action == "refresh":
            await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=cb.message.reply_markup)
        else:
            await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=None)
    
    # Update creator's message if available
    if event.creator_message_id and event.creator_id != cb.from_user.id:
        member_statuses = "\n".join(lines) if lines else "No members"
        creator_text = f"Event `{event_id}`\n\nУчастники:\n{member_statuses}"
        try:
            await bot.edit_message_text(
                chat_id=event.creator_id,
                message_id=event.creator_message_id,
                text=creator_text,
                parse_mode="Markdown",
            )
        except Exception:
            # Message might be deleted or unavailable
            pass
    
    await cb.answer("OK")

