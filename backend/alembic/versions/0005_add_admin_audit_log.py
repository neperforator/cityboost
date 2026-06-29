"""add admin_action_log table

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-28 16:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_action_log",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_action_log_admin_id", "admin_action_log", ["admin_id"])
    op.create_index("ix_admin_action_log_action", "admin_action_log", ["action"])
    op.create_index("ix_admin_action_log_created_at", "admin_action_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("admin_action_log")
