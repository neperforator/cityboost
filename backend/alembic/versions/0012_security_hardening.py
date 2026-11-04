"""security hardening: token version, verification attempts, indexes

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-05 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # В БД теперь хранится HMAC-хеш кода подтверждения, а не сам код.
    op.alter_column(
        "users",
        "verification_code",
        existing_type=sa.String(6),
        type_=sa.String(255),
        existing_nullable=True,
    )
    op.add_column(
        "users",
        sa.Column(
            "verification_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("verification_last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    # Индексы на внешние ключи, которые используются в фильтрах и JOIN'ах.
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_user_id ON tickets (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_assigned_to ON tickets (assigned_to)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_files_ticket_id ON ticket_files (ticket_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_history_ticket_id ON ticket_history (ticket_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_history_changed_by ON ticket_history (changed_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_comments_ticket_id ON ticket_comments (ticket_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_comments_author_id ON ticket_comments (author_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ticket_comments_author_id")
    op.execute("DROP INDEX IF EXISTS ix_ticket_comments_ticket_id")
    op.execute("DROP INDEX IF EXISTS ix_ticket_history_changed_by")
    op.execute("DROP INDEX IF EXISTS ix_ticket_history_ticket_id")
    op.execute("DROP INDEX IF EXISTS ix_ticket_files_ticket_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_assigned_to")
    op.execute("DROP INDEX IF EXISTS ix_tickets_user_id")

    op.drop_column("users", "token_version")
    op.drop_column("users", "verification_last_sent_at")
    op.drop_column("users", "verification_attempts")
    op.alter_column(
        "users",
        "verification_code",
        existing_type=sa.String(255),
        type_=sa.String(6),
        existing_nullable=True,
    )
