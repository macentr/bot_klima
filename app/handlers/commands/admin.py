"""Admin panel handlers."""
from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from app.repositories.uow import UnitOfWork
from app.services.admin import AdminService
from app.ui.keyboards import AdminCb, admin_panel_kb
from app.handlers.middlewares.admin import AdminOnlyMiddleware


logger = logging.getLogger(__name__)
router = Router(name="admin")
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


class BroadcastStates(StatesGroup):
    waiting_message = State()


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    """Open admin panel."""
    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(AdminCb.filter())
async def admin_action(cb: CallbackQuery, callback_data: AdminCb, uow: UnitOfWork, state: FSMContext) -> None:
    """Handle admin panel actions."""
    action = callback_data.action
    
    if action == "stats":
        # Show current month stats
        now = datetime.now()
        async with uow:
            assert uow.session is not None
            admin_service = AdminService(uow.session)
            stats = await admin_service.get_monthly_stats(now.year, now.month)
        
        # Format events by type
        events_text = "\n".join([
            f"  • {event_type}: {count}"
            for event_type, count in stats.events_by_type.items()
        ]) or "  Нет событий"
        
        stats_text = (
            f"📊 <b>Статистика за {now.strftime('%B %Y')}</b>\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"  • Всего зарегистрировано: {stats.total_users}\n"
            f"  • Активных в месяце: {stats.active_users}\n\n"
            f"🏠 <b>Комнаты:</b> {stats.total_rooms}\n\n"
            f"🎉 <b>События:</b> {stats.total_events}\n"
            f"{events_text}"
        )
        
        if cb.message:
            await cb.message.edit_text(stats_text, parse_mode="HTML", reply_markup=admin_panel_kb())
        await cb.answer()
        return
    
    if action == "broadcast":
        await state.set_state(BroadcastStates.waiting_message)
        if cb.message:
            await cb.message.edit_text(
                "📢 <b>Массовая рассылка</b>\n\n"
                "Отправьте сообщение, которое нужно разослать всем пользователям.\n"
                "Для отмены отправьте /cancel",
                parse_mode="HTML"
            )
        await cb.answer()
        return
    
    await cb.answer("Неизвестное действие", show_alert=True)


@router.message(BroadcastStates.waiting_message, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext) -> None:
    """Cancel broadcast."""
    await state.clear()
    await message.answer(
        "❌ Рассылка отменена.",
        reply_markup=admin_panel_kb()
    )


@router.message(BroadcastStates.waiting_message)
async def send_broadcast(message: Message, uow: UnitOfWork, state: FSMContext, bot: Bot) -> None:
    """Send broadcast message to all users."""
    await state.clear()
    
    # Get all user IDs
    async with uow:
        assert uow.session is not None
        admin_service = AdminService(uow.session)
        user_ids = await admin_service.get_all_user_ids()
    
    # Send status message
    status_msg = await message.answer(
        f"📤 Начинаю рассылку {len(user_ids)} пользователям...",
        reply_markup=admin_panel_kb()
    )
    
    # Broadcast
    success_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            # Forward the admin's message to each user
            if message.text:
                await bot.send_message(chat_id=user_id, text=message.text)
            elif message.photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await bot.send_video(
                    chat_id=user_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            elif message.document:
                await bot.send_document(
                    chat_id=user_id,
                    document=message.document.file_id,
                    caption=message.caption
                )
            else:
                # Copy any other message type
                await message.copy_to(chat_id=user_id)
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to user {user_id}: {e}")
            failed_count += 1
    
    # Update status
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"📨 Отправлено: {success_count}\n"
        f"❌ Не доставлено: {failed_count}",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )
