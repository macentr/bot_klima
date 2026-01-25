from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from app.domain.enums.event import EventType, ParticipationState
from app.domain.enums.room import RoomRole
from app.domain.enums.user import UserGlobalStatus
from app.domain.exceptions import ConflictError
from app.repositories.events import EventRepository, ParticipationRepository
from app.repositories.rooms import RoomMemberRepository, RoomRepository
from app.repositories.users import UserRepository
from app.services.access import AccessControl


class EventService:
    def __init__(
        self,
        *,
        events: EventRepository,
        participations: ParticipationRepository,
        rooms: RoomRepository,
        room_members: RoomMemberRepository,
        users: UserRepository,
        access: AccessControl,
    ) -> None:
        self._events = events
        self._participations = participations
        self._rooms = rooms
        self._room_members = room_members
        self._users = users
        self._access = access

    async def create_event(
        self,
        *,
        room_id: uuid.UUID,
        creator_id: int,
        event_type: EventType,
        auto_close_minutes: int | None,
    ) -> uuid.UUID:
        await self._access.require_role_at_least(
            room_id=room_id,
            user_id=creator_id,
            allowed={RoomRole.OWNER, RoomRole.ADMIN, RoomRole.MEMBER},
            action="create_event",
        )

        room = await self._rooms.require(room_id)
        if str(room.state) != "ACTIVE":
            raise ConflictError("События можно создавать только в активных комнатах")

        # Блокируем частое создание событий: не чаще одного раза в 5 минут.
        last_event = await self._events.get_last_event_in_room(room_id)
        if last_event is not None:
            now = datetime.now(timezone.utc)
            elapsed = now - last_event.created_at
            cooldown = timedelta(minutes=5)
            if elapsed < cooldown:
                remaining = cooldown - elapsed
                minutes_left = int(remaining.total_seconds() // 60)
                seconds_left = int(remaining.total_seconds() % 60)
                raise ConflictError(
                    f"Новое событие можно создать через {minutes_left} мин {seconds_left} сек после предыдущего"
                )

        close_at = None
        if auto_close_minutes is not None:
            close_at = datetime.now(timezone.utc) + timedelta(minutes=auto_close_minutes)

        try:
            event = await self._events.create_open_event(
                room_id=room_id,
                creator_id=creator_id,
                event_type=event_type,
                close_at=close_at,
            )
            member_ids = await self._room_members.list_member_ids(room_id=room_id)
            # Disabled users are excluded from everything.
            # We'll filter by existing users table state for safety.
            # ParticipationRepository will treat VACATION users as VACATION automatically.
            active_or_vacation_ids: list[int] = []
            for uid in member_ids:
                u = await self._users.get(uid)
                if u is None:
                    continue
                if u.global_status == UserGlobalStatus.DISABLED:
                    continue
                active_or_vacation_ids.append(uid)

            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Event creation: room_id={room_id}, creator_id={creator_id}")
            logger.debug(f"  All members: {member_ids}")
            logger.debug(f"  Active/Vacation members: {active_or_vacation_ids}")

            await self._participations.create_for_members(
                event_id=event.id,
                member_ids=active_or_vacation_ids,
                creator_id=creator_id,
            )
            return event.id
        except IntegrityError as e:
            # Partial unique index for OPEN per room.
            raise ConflictError("В этой комнате уже есть открытое событие") from e

    async def respond(
        self,
        *,
        event_id: uuid.UUID,
        user_id: int,
        state: ParticipationState,
    ) -> ParticipationState:
        # State transitions are idempotent; repo enforces VACATION rule.
        return await self._participations.set_state_idempotent(
            event_id=event_id,
            user_id=user_id,
            new_state=state,
        )

