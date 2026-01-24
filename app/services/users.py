from __future__ import annotations

from aiogram.types import User as TgUser

from app.domain.enums.user import UserGlobalStatus
from app.repositories.users import UserRepository


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def upsert_from_telegram(self, tg_user: TgUser) -> None:
        display_name = " ".join(x for x in [tg_user.first_name, tg_user.last_name] if x) or "Unknown"
        await self._users.upsert(
            tg_user.id,
            username=tg_user.username,
            display_name=display_name,
        )

    async def set_vacation(self, telegram_id: int, *, enabled: bool) -> None:
        if enabled:
            await self._users.set_global_status(telegram_id, status=UserGlobalStatus.VACATION)
        else:
            await self._users.set_global_status(telegram_id, status=UserGlobalStatus.ACTIVE)

