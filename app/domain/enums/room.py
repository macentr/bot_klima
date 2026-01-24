from __future__ import annotations

from enum import StrEnum


class RoomState(StrEnum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class RoomRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

