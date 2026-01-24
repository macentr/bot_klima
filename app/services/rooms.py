from __future__ import annotations

import uuid

from app.domain.enums.room import RoomRole, RoomState
from app.domain.exceptions import AccessDeniedError, ConflictError
from app.repositories.rooms import RoomMemberRepository, RoomRepository
from app.utils.invite_code import generate_invite_code


class RoomService:
    def __init__(self, rooms: RoomRepository, members: RoomMemberRepository) -> None:
        self._rooms = rooms
        self._members = members

    async def create_room(self, *, name: str, owner_id: int) -> uuid.UUID:
        # Generate unique invite code
        invite_code = generate_invite_code()
        room = await self._rooms.create(name=name, owner_id=owner_id, invite_code=invite_code)
        # Room becomes active immediately for MVP.
        room.state = RoomState.ACTIVE
        await self._members.upsert_member(room_id=room.id, user_id=owner_id, role=RoomRole.OWNER)
        return room.id

    async def join_room(self, *, room_id: uuid.UUID, user_id: int) -> None:
        room = await self._rooms.require(room_id)
        if room.state != RoomState.ACTIVE:
            raise ConflictError("room is not active")
        await self._members.upsert_member(room_id=room_id, user_id=user_id, role=RoomRole.MEMBER)

    async def join_by_invite_code(self, *, invite_code: str, user_id: int) -> uuid.UUID:
        """Join room using invite code."""
        room = await self._rooms.get_by_invite_code(invite_code)
        if room is None:
            raise ConflictError("invalid invite code")
        if room.state != RoomState.ACTIVE:
            raise ConflictError("room is not active")
        await self._members.upsert_member(room_id=room.id, user_id=user_id, role=RoomRole.MEMBER)
        return room.id

    async def delete_room(self, *, room_id: uuid.UUID, user_id: int) -> None:
        """Delete room, only owner can delete."""
        room = await self._rooms.require(room_id)
        role = await self._members.get_role(room_id=room_id, user_id=user_id)
        if role != RoomRole.OWNER:
            raise AccessDeniedError("only room owner can delete room")
        await self._rooms.delete_room(room_id)

