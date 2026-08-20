"""improve ticket_history and admin_action_log

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-17 18:40:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ticket_history: событийный лог (action + details) ---
    op.add_column(
        "ticket_history",
        sa.Column("action", sa.String(30), nullable=False, server_default="STATUS_CHANGED"),
    )
    op.add_column(
        "ticket_history",
        sa.Column("details", sa.Text(), nullable=True),
    )
    op.create_index("ix_ticket_history_action", "ticket_history", ["action"])

    # --- admin_action_log: имя цели (заголовок заявки / имя пользователя) ---
    op.add_column(
        "admin_action_log",
        sa.Column("target_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("admin_action_log", "target_name")
    op.drop_index("ix_ticket_history_action", table_name="ticket_history")
    op.drop_column("ticket_history", "details")
    op.drop_column("ticket_history", "action")