"""add is_verified, verification_code, verification_code_expires to users

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-29 14:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "verification_code",
            sa.String(6),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "verification_code_expires",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "verification_code_expires")
    op.drop_column("users", "verification_code")
    op.drop_column("users", "is_verified")
