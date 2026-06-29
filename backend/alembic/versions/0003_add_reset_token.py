"""add reset_token and reset_token_expires to users

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-28 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "reset_token",
            sa.String(255),
            nullable=True,
            unique=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "reset_token_expires",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index("ix_users_reset_token", "users", ["reset_token"])


def downgrade() -> None:
    op.drop_index("ix_users_reset_token", table_name="users")
    op.drop_column("users", "reset_token_expires")
    op.drop_column("users", "reset_token")
