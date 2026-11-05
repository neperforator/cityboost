"""add notify_author to tickets

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-05 18:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column(
            "notify_author",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="Отправлять автору email-уведомления по заявке",
        ),
    )


def downgrade() -> None:
    op.drop_column("tickets", "notify_author")
