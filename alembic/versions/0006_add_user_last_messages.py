"""
Add last menu/invite message ids to users

Revision ID: 0006_add_user_last_messages
Revises: 0005_restore_owner_roles
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_add_user_last_messages"
down_revision = "0005_restore_owner_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_menu_message_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("last_invite_message_id", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_invite_message_id")
    op.drop_column("users", "last_menu_message_id")
