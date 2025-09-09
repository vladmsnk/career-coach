"""Change collected_data column type from JSON to JSONB

Revision ID: 0005_jsonb_collected_data
Revises: 0004_add_module_fields
Create Date: 2024-01-15 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, JSONB


# revision identifiers, used by Alembic.
revision = '0005_jsonb_collected_data'
down_revision = '0004_add_module_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change collected_data column type from JSON to JSONB for better performance"""
    # Change column type from JSON to JSONB
    # PostgreSQL can convert JSON to JSONB automatically
    op.alter_column(
        'chat_sessions',
        'collected_data',
        type_=JSONB(),
        postgresql_using='collected_data::JSONB'
    )


def downgrade() -> None:
    """Revert collected_data column type from JSONB back to JSON"""
    # Change column type from JSONB back to JSON
    op.alter_column(
        'chat_sessions',
        'collected_data',
        type_=JSON(),
        postgresql_using='collected_data::JSON'
    )
