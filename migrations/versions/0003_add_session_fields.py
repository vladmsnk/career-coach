from alembic import op
import sqlalchemy as sa

revision = "0003_add_session_fields"
down_revision = "0002_create_chat_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("question_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("answers_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("chat_sessions", "status", server_default=None)
    op.alter_column("chat_sessions", "question_index", server_default=None)
    op.alter_column("chat_sessions", "answers_count", server_default=None)


def downgrade() -> None:
    op.drop_column("chat_sessions", "answers_count")
    op.drop_column("chat_sessions", "question_index")
    op.drop_column("chat_sessions", "status")
