"""
Add custom event type and custom_description field

Revision ID: 0008_add_custom_event_type
Revises: 0007_add_user_is_admin
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_add_custom_event_type"
down_revision = "0007_add_user_is_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add CUSTOM to event_type enum
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'CUSTOM'")
    
    # Add custom_description column
    op.add_column("events", sa.Column("custom_description", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "custom_description")
    # Note: PostgreSQL doesn't support removing enum values easily
