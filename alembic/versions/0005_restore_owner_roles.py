"""restore owner roles for all rooms

Revision ID: 0005_restore_owner_roles
Revises: 0004_add_open_event_id
Create Date: 2026-01-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0005_restore_owner_roles"
down_revision = "0004_add_open_event_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure all room owners have OWNER role in room_members
    # This fixes cases where users lost their OWNER role after rejoining
    connection = op.get_bind()
    
    # For each room, ensure the owner (from rooms.owner_id) has OWNER role in room_members
    connection.execute(sa.text("""
        UPDATE room_members
        SET role = 'OWNER'
        WHERE (room_id, user_id) IN (
            SELECT r.id, r.owner_id
            FROM rooms r
        )
    """))


def downgrade() -> None:
    # No downgrade needed - this is a data fix
    pass
