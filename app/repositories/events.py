from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.event import EventState, EventType, ParticipationState
from app.domain.enums.user import UserGlobalStatus
from app.domain.exceptions import ConflictError, NotFoundError
from app.repositories.db.models import EventModel, ParticipationModel, RoomModel, UserModel


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: uuid.UUID) -> EventModel | None:
        return await self._session.get(EventModel, event_id)

    async def require(self, event_id: uuid.UUID) -> EventModel:
        e = await self.get(event_id)
        if e is None:
            raise NotFoundError(f"event {event_id} not found")
        return e

    async def find_open_in_room(self, room_id: uuid.UUID) -> EventModel | None:
        res = await self._session.execute(
            select(EventModel).where(EventModel.room_id == room_id, EventModel.state == EventState.OPEN)
        )
        return res.scalar_one_or_none()

    async def create_open_event(
        self,
        *,
        room_id: uuid.UUID,
        creator_id: int,
        event_type: EventType,
        close_at: datetime | None,
    ) -> EventModel:
        """
        Creates event in OPEN state. Uniqueness "one OPEN per room" is enforced by DB index.
        """
        # Generate UUID on Python side so it's available before flush/commit.
        event = EventModel(
            id=uuid.uuid4(),
            room_id=room_id,
            creator_id=creator_id,
            type=event_type,
            state=EventState.OPEN,
            close_at=close_at,
        )
        self._session.add(event)
        return event

    async def close_event(self, event_id: uuid.UUID) -> None:
        res = await self._session.execute(
            update(EventModel)
            .where(EventModel.id == event_id, EventModel.state != EventState.CLOSED)
            .values(state=EventState.CLOSED)
        )
        if res.rowcount == 0:
            raise NotFoundError(f"event {event_id} not found or already closed")

    async def list_expired_open_events(self, *, now: datetime | None = None, limit: int = 100) -> list[uuid.UUID]:
        now = now or datetime.now(timezone.utc)
        res = await self._session.execute(
            select(EventModel.id)
            .where(
                EventModel.state == EventState.OPEN,
                EventModel.close_at.is_not(None),
                EventModel.close_at <= now,
            )
            .order_by(EventModel.close_at.asc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def delete_event(self, event_id: uuid.UUID) -> None:
        await self._session.execute(delete(EventModel).where(EventModel.id == event_id))

    async def ensure_room_active(self, room_id: uuid.UUID) -> None:
        res = await self._session.execute(select(RoomModel.state).where(RoomModel.id == room_id))
        state = res.scalar_one_or_none()
        if state is None:
            raise NotFoundError(f"room {room_id} not found")
        # RoomState is imported in service layer; here we just compare string to avoid import cycle.
        if str(state) != "ACTIVE":
            raise ConflictError("events can exist only in ACTIVE rooms")


class ParticipationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_for_members(
        self,
        *,
        event_id: uuid.UUID,
        member_ids: list[int],
        creator_id: int,
    ) -> None:
        """
        Create participation records for all members.
        ACTIVE -> PENDING, VACATION -> VACATION, DISABLED excluded by caller.
        Creator is ACCEPTED (idempotent by primary key).
        """
        if not member_ids:
            return

        res = await self._session.execute(
            select(UserModel.id, UserModel.global_status).where(UserModel.id.in_(member_ids))
        )
        rows = res.all()

        to_add: list[ParticipationModel] = []
        for user_id, gstatus in rows:
            if user_id == creator_id:
                state = ParticipationState.ACCEPTED
            elif gstatus == UserGlobalStatus.VACATION:
                state = ParticipationState.VACATION
            else:
                state = ParticipationState.PENDING
            to_add.append(ParticipationModel(event_id=event_id, user_id=user_id, state=state))

        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"create_for_members: adding {len(to_add)} participation records for event_id={event_id}")
        self._session.add_all(to_add)
        await self._session.flush()
        logger.debug(f"create_for_members: flush completed")

    async def set_state_idempotent(
        self,
        *,
        event_id: uuid.UUID,
        user_id: int,
        new_state: ParticipationState,
    ) -> ParticipationState:
        """
        Idempotent state transition:
        - If already in new_state -> no-op.
        - VACATION cannot be changed to other states.
        """
        p = await self._session.get(ParticipationModel, {"event_id": event_id, "user_id": user_id})
        if p is None:
            raise NotFoundError("participation not found")
        if p.state == ParticipationState.VACATION and new_state != ParticipationState.VACATION:
            raise ConflictError("vacation user cannot change participation state")
        p.state = new_state
        return p.state

    async def list_for_event(self, event_id: uuid.UUID) -> list[ParticipationModel]:
        res = await self._session.execute(
            select(ParticipationModel).where(ParticipationModel.event_id == event_id)
        )
        return list(res.scalars().all())

    async def get_participation(self, *, event_id: uuid.UUID, user_id: int) -> ParticipationModel | None:
        """Get single participation record."""
        return await self._session.get(ParticipationModel, {"event_id": event_id, "user_id": user_id})

    async def list_with_users(
        self,
        event_id: uuid.UUID,
    ) -> list[tuple[ParticipationModel, UserModel]]:
        """
        Returns participation with attached user rows for rich UI rendering.
        """
        import logging
        logger = logging.getLogger(__name__)
        res = await self._session.execute(
            select(ParticipationModel, UserModel)
            .join(UserModel, UserModel.id == ParticipationModel.user_id)
            .where(ParticipationModel.event_id == event_id)
        )
        results = list(res.all())
        logger.debug(f"list_with_users: event_id={event_id}, found {len(results)} participation+user rows")
        return results
