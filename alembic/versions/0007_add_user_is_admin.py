"""
Add is_admin field to users table

Revision ID: 0007_add_user_is_admin
Revises: 0006_add_user_last_messages
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_add_user_is_admin"
down_revision = "0006_add_user_last_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column with default False
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"))
    
    # Set admin flag for specific user ID
    op.execute("UPDATE users SET is_admin = true WHERE id = 509402010")


def downgrade() -> None:
    op.drop_column("users", "is_admin")
