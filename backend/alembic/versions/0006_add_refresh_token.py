"""add refresh_token_hash and refresh_token_expires to users

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-29 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "refresh_token_hash",
            sa.String(255),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "refresh_token_expires",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "refresh_token_expires")
    op.drop_column("users", "refresh_token_hash")
