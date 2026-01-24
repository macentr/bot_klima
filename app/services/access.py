from __future__ import annotations

import uuid

from app.domain.enums.room import RoomRole
from app.domain.exceptions import AccessDeniedError
from app.repositories.rooms import RoomMemberRepository


class AccessControl:
    """
    Centralized RBAC checks.
    """

    def __init__(self, room_members: RoomMemberRepository) -> None:
        self._room_members = room_members

    async def require_role_at_least(
        self,
        *,
        room_id: uuid.UUID,
        user_id: int,
        allowed: set[RoomRole],
        action: str,
    ) -> RoomRole:
        role = await self._room_members.get_role(room_id=room_id, user_id=user_id)
        if role is None:
            raise AccessDeniedError(f"not a member: {action}")
        if role not in allowed:
            raise AccessDeniedError(f"forbidden: {action}")
        return role

