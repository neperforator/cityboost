"""add trigram indexes for admin ticket search

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-04 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Поиск по заявкам: ILIKE '%...%' по текстовым полям.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tickets_title_trgm "
        "ON tickets USING gin (title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tickets_description_trgm "
        "ON tickets USING gin (description gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tickets_address_trgm "
        "ON tickets USING gin (address gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tickets_close_reason_trgm "
        "ON tickets USING gin (close_reason gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tickets_id_trgm "
        "ON tickets USING gin ((id::text) gin_trgm_ops)"
    )

    # Поиск по заявителю / исполнителю.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_name_trgm "
        "ON users USING gin (name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_email_trgm "
        "ON users USING gin (email gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_email_trgm")
    op.execute("DROP INDEX IF EXISTS ix_users_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_tickets_id_trgm")
    op.execute("DROP INDEX IF EXISTS ix_tickets_close_reason_trgm")
    op.execute("DROP INDEX IF EXISTS ix_tickets_address_trgm")
    op.execute("DROP INDEX IF EXISTS ix_tickets_description_trgm")
    op.execute("DROP INDEX IF EXISTS ix_tickets_title_trgm")
