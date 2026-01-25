from __future__ import annotations

import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.room import RoomRole, RoomState
from app.domain.exceptions import ConflictError, NotFoundError
from app.repositories.db.models import RoomMemberModel, RoomModel


class RoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, room_id: uuid.UUID) -> RoomModel | None:
        return await self._session.get(RoomModel, room_id)

    async def require(self, room_id: uuid.UUID) -> RoomModel:
        room = await self.get(room_id)
        if room is None:
            raise NotFoundError(f"Комната {room_id} не найдена")
        return room

    async def create(self, *, name: str, owner_id: int, invite_code: str | None = None) -> RoomModel:
        # Generate UUID on Python side so it's available before flush/commit.
        room = RoomModel(id=uuid.uuid4(), name=name, owner_id=owner_id, state=RoomState.CREATED, invite_code=invite_code)
        self._session.add(room)
        # Membership is created separately to keep transaction explicit in service.
        return room

    async def get_by_invite_code(self, invite_code: str) -> RoomModel | None:
        """Find room by invite code."""
        res = await self._session.execute(
            select(RoomModel).where(RoomModel.invite_code == invite_code.upper())
        )
        return res.scalar_one_or_none()

    async def set_state(self, room_id: uuid.UUID, *, state: RoomState) -> None:
        res = await self._session.execute(
            update(RoomModel).where(RoomModel.id == room_id).values(state=state)
        )
        if res.rowcount == 0:
            raise NotFoundError(f"Комната {room_id} не найдена")

    async def delete_room(self, room_id: uuid.UUID) -> None:
        await self._session.execute(delete(RoomModel).where(RoomModel.id == room_id))

    async def list_rooms_for_user(self, *, user_id: int) -> list[RoomModel]:
        res = await self._session.execute(
            select(RoomModel)
            .join(RoomMemberModel, RoomMemberModel.room_id == RoomModel.id)
            .where(RoomMemberModel.user_id == user_id, RoomModel.state != RoomState.ARCHIVED)
            .order_by(RoomModel.name.asc())
        )
        return list(res.scalars().all())


class RoomMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role(self, *, room_id: uuid.UUID, user_id: int) -> RoomRole | None:
        res = await self._session.execute(
            select(RoomMemberModel.role).where(
                RoomMemberModel.room_id == room_id, RoomMemberModel.user_id == user_id
            )
        )
        return res.scalar_one_or_none()

    async def add_member(
        self,
        *,
        room_id: uuid.UUID,
        user_id: int,
        role: RoomRole = RoomRole.MEMBER,
    ) -> RoomMemberModel:
        """
        Idempotent-ish: if already exists, raises ConflictError to force service to decide.
        """
        existing = await self._session.get(RoomMemberModel, {"room_id": room_id, "user_id": user_id})
        if existing is not None:
            raise ConflictError("Пользователь уже состоит в комнате")
        m = RoomMemberModel(room_id=room_id, user_id=user_id, role=role)
        self._session.add(m)
        return m

    async def upsert_member(
        self,
        *,
        room_id: uuid.UUID,
        user_id: int,
        role: RoomRole,
    ) -> RoomMemberModel:
        """
        Idempotent membership: create if missing, otherwise update role only if not downgrading.
        Prevents downgrading OWNER to MEMBER if they rejoin their own room.
        """
        m = await self._session.get(RoomMemberModel, {"room_id": room_id, "user_id": user_id})
        if m is None:
            m = RoomMemberModel(room_id=room_id, user_id=user_id, role=role)
            self._session.add(m)
            return m
        # Don't downgrade: if current role is higher, keep it
        # Role hierarchy: OWNER (0) > ADMIN (1) > MEMBER (2)
        role_order = {RoomRole.OWNER: 0, RoomRole.ADMIN: 1, RoomRole.MEMBER: 2}
        if role_order[m.role] < role_order[role]:
            # Current role is higher, don't change
            return m
        m.role = role
        return m

    async def remove_member(self, *, room_id: uuid.UUID, user_id: int) -> None:
        await self._session.execute(
            delete(RoomMemberModel).where(
                RoomMemberModel.room_id == room_id, RoomMemberModel.user_id == user_id
            )
        )

    async def list_member_ids(self, *, room_id: uuid.UUID) -> list[int]:
        res = await self._session.execute(
            select(RoomMemberModel.user_id).where(RoomMemberModel.room_id == room_id)
        )
        return list(res.scalars().all())

