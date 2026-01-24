"""add invite_code to rooms

Revision ID: 0003_add_invite_code
Revises: 0002_add_creator_message_id
Create Date: 2026-01-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_add_invite_code"
down_revision = "0002_add_creator_message_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rooms", sa.Column("invite_code", sa.String(10), nullable=True, unique=True))


def downgrade() -> None:
    op.drop_column("rooms", "invite_code")
