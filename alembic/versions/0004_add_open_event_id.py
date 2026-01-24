"""add open_event_id to rooms

Revision ID: 0004_add_open_event_id
Revises: 0003_add_invite_code
Create Date: 2026-01-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_add_open_event_id"
down_revision = "0003_add_invite_code"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rooms", sa.Column("open_event_id", sa.dialects.postgresql.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_rooms_open_event_id",
        "rooms",
        "events",
        ["open_event_id"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_rooms_open_event_id", "rooms", type_="foreignkey")
    op.drop_column("rooms", "open_event_id")
