from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    SMOKE = "SMOKE"
    COFFEE = "COFFEE"
    WALK = "WALK"
    CUSTOM = "CUSTOM"


class EventState(StrEnum):
    CREATED = "CREATED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ParticipationState(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    LATER = "LATER"
    DECLINED = "DECLINED"
    VACATION = "VACATION"

