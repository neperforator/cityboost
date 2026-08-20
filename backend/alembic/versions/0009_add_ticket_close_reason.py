"""add close_reason to tickets

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-18 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("close_reason", sa.Text(), nullable=True, comment="Причина закрытия заявки"),
    )


def downgrade() -> None:
    op.drop_column("tickets", "close_reason")
