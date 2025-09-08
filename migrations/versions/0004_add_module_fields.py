"""Add module fields to chat_sessions

Revision ID: 0004_add_module_fields
Revises: 0003_add_session_fields
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '0004_add_module_fields'
down_revision = '0003_add_session_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add current_module column with default value
    op.add_column(
        "chat_sessions",
        sa.Column("current_module", sa.String(length=20), nullable=False, server_default="context"),
    )
    
    # Add collected_data column with default empty JSON
    op.add_column(
        "chat_sessions", 
        sa.Column("collected_data", JSON(), nullable=False, server_default="{}")
    )
    
    # Remove server_default after adding columns (best practice)
    op.alter_column("chat_sessions", "current_module", server_default=None)
    op.alter_column("chat_sessions", "collected_data", server_default=None)


def downgrade() -> None:
    # Remove the added columns
    op.drop_column("chat_sessions", "collected_data")
    op.drop_column("chat_sessions", "current_module")
