"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column(
            "global_status",
            sa.Enum("ACTIVE", "VACATION", "DISABLED", name="user_global_status"),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column("vacation_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )

    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("CREATED", "ACTIVE", "ARCHIVED", name="room_state"),
            server_default="CREATED",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT", name=op.f("fk_rooms_owner_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rooms")),
    )

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creator_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.Enum("SMOKE", "COFFEE", "WALK", "CUSTOM", name="event_type"), nullable=False),
        sa.Column(
            "state",
            sa.Enum("CREATED", "OPEN", "CLOSED", name="event_state"),
            server_default="CREATED",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("close_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="RESTRICT", name=op.f("fk_events_creator_id_users")),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE", name=op.f("fk_events_room_id_rooms")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index("ix_events_close_at", "events", ["close_at"], unique=False)
    op.create_index(
        "uq_open_event_per_room",
        "events",
        ["room_id"],
        unique=True,
        postgresql_where=sa.text("state = 'OPEN'"),
    )

    op.create_table(
        "room_members",
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("OWNER", "ADMIN", "MEMBER", name="room_role"),
            server_default="MEMBER",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE", name=op.f("fk_room_members_room_id_rooms")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_room_members_user_id_users")),
        sa.PrimaryKeyConstraint("room_id", "user_id", name=op.f("pk_room_members")),
    )
    op.create_index(
        "uq_room_owner_role",
        "room_members",
        ["room_id"],
        unique=True,
        postgresql_where=sa.text("role = 'OWNER'"),
    )

    op.create_table(
        "participations",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("PENDING", "ACCEPTED", "LATER", "DECLINED", "VACATION", name="participation_state"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint("state <> 'VACATION' OR note IS NULL", name="ck_vacation_has_no_note"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE", name=op.f("fk_participations_event_id_events")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_participations_user_id_users")),
        sa.PrimaryKeyConstraint("event_id", "user_id", name=op.f("pk_participations")),
        sa.UniqueConstraint("event_id", "user_id", name="uq_participation_event_user"),
    )


def downgrade() -> None:
    op.drop_table("participations")
    op.drop_index("uq_room_owner_role", table_name="room_members")
    op.drop_table("room_members")
    op.drop_index("uq_open_event_per_room", table_name="events")
    op.drop_index("ix_events_close_at", table_name="events")
    op.drop_table("events")
    op.drop_table("rooms")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS participation_state")
    op.execute("DROP TYPE IF EXISTS event_state")
    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS room_role")
    op.execute("DROP TYPE IF EXISTS room_state")
    op.execute("DROP TYPE IF EXISTS user_global_status")

