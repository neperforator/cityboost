"""add admin two-factor authentication fields

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-04 15:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("two_factor_code_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("two_factor_expires", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "two_factor_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("two_factor_last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "two_factor_last_sent_at")
    op.drop_column("users", "two_factor_attempts")
    op.drop_column("users", "two_factor_expires")
    op.drop_column("users", "two_factor_code_hash")
