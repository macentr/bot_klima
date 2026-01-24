from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums.event import EventState, EventType, ParticipationState
from app.domain.enums.room import RoomRole, RoomState
from app.domain.enums.user import UserGlobalStatus
from app.repositories.db.base import Base


class UserModel(Base):
    __tablename__ = "users"

    # Telegram user id
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    global_status: Mapped[UserGlobalStatus] = mapped_column(
        Enum(UserGlobalStatus, name="user_global_status"),
        nullable=False,
        server_default=UserGlobalStatus.ACTIVE.value,
    )
    vacation_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[list["RoomMemberModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RoomModel(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    invite_code: Mapped[str | None] = mapped_column(String(10), nullable=True, unique=True)

    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    state: Mapped[RoomState] = mapped_column(
        Enum(RoomState, name="room_state"),
        nullable=False,
        server_default=RoomState.CREATED.value,
    )

    members: Mapped[list["RoomMemberModel"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    events: Mapped[list["EventModel"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RoomMemberModel(Base):
    __tablename__ = "room_members"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped[RoomRole] = mapped_column(
        Enum(RoomRole, name="room_role"),
        nullable=False,
        server_default=RoomRole.MEMBER.value,
    )

    room: Mapped["RoomModel"] = relationship(back_populates="members")
    user: Mapped["UserModel"] = relationship(back_populates="memberships")

    __table_args__ = (
        # Exactly one OWNER per room (enforced via partial unique index).
        Index(
            "uq_room_owner_role",
            "room_id",
            unique=True,
            postgresql_where=(role == RoomRole.OWNER),
        ),
    )


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    creator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type"), nullable=False)
    state: Mapped[EventState] = mapped_column(
        Enum(EventState, name="event_state"),
        nullable=False,
        server_default=EventState.CREATED.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Message ID of the creator's message (for updating event status)
    creator_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    room: Mapped["RoomModel"] = relationship(back_populates="events")
    participations: Mapped[list["ParticipationModel"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # At most one OPEN event per room (Postgres partial unique index).
        Index(
            "uq_open_event_per_room",
            "room_id",
            unique=True,
            postgresql_where=(state == EventState.OPEN),
        ),
        Index("ix_events_close_at", "close_at"),
    )


class ParticipationModel(Base):
    __tablename__ = "participations"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    state: Mapped[ParticipationState] = mapped_column(
        Enum(ParticipationState, name="participation_state"),
        nullable=False,
    )

    # Optional per-user comment/extra message later (kept for future extension).
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    event: Mapped["EventModel"] = relationship(back_populates="participations")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_participation_event_user"),
        CheckConstraint(
            "state <> 'VACATION' OR note IS NULL",
            name="ck_vacation_has_no_note",
        ),
    )

