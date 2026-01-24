"""add creator_message_id to events

Revision ID: 0002_add_creator_message_id
Revises: 0001_initial
Create Date: 2026-01-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0002_add_creator_message_id"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("creator_message_id", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "creator_message_id")
