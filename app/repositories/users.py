from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.user import UserGlobalStatus
from app.domain.exceptions import NotFoundError
from app.repositories.db.models import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, telegram_id: int) -> UserModel | None:
        return await self._session.get(UserModel, telegram_id)

    async def require(self, telegram_id: int) -> UserModel:
        user = await self.get(telegram_id)
        if user is None:
            raise NotFoundError(f"Пользователь {telegram_id} не найден")
        return user

    async def upsert(
        self,
        telegram_id: int,
        *,
        username: str | None,
        display_name: str,
    ) -> UserModel:
        """
        Idempotent create/update based on telegram_id.
        """
        user = await self.get(telegram_id)
        if user is None:
            user = UserModel(id=telegram_id, username=username, display_name=display_name)
            self._session.add(user)
            return user

        user.username = username
        user.display_name = display_name
        return user

    async def set_global_status(
        self,
        telegram_id: int,
        *,
        status: UserGlobalStatus,
        vacation_until=None,
    ) -> None:
        res = await self._session.execute(
            update(UserModel)
            .where(UserModel.id == telegram_id)
            .values(global_status=status, vacation_until=vacation_until)
        )
        if res.rowcount == 0:
            raise NotFoundError(f"Пользователь {telegram_id} не найден")

    async def list_active_ids(self) -> list[int]:
        res = await self._session.execute(
            select(UserModel.id).where(UserModel.global_status == UserGlobalStatus.ACTIVE)
        )
        return list(res.scalars().all())

