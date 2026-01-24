from __future__ import annotations

import asyncio
from collections.abc import Iterable

from aiogram import Bot


class NotificationService:
    """
    Async sender with simple rate limiting.

    NOTE: We intentionally do NOT broadcast on every participation change.
    We only notify on event creation; everything else is fetched on-demand via Refresh.
    """

    def __init__(self, bot: Bot, *, max_parallel: int = 10) -> None:
        self._bot = bot
        self._sem = asyncio.Semaphore(max_parallel)

    async def send_many(self, user_ids: Iterable[int], *, text: str, reply_markup=None) -> None:
        async def _send_one(uid: int) -> None:
            async with self._sem:
                try:
                    await self._bot.send_message(uid, text, reply_markup=reply_markup)
                except Exception:
                    # Ignore individual failures (blocked bot, etc.)
                    return

        await asyncio.gather(*[_send_one(uid) for uid in user_ids])

