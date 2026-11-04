"""audit: FK for admin_id and index for target_id

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-05 13:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # admin_id всегда ссылается на users.id — закрываем возможность
    # появления «висячих» записей аудита.
    op.create_foreign_key(
        "fk_admin_action_log_admin_id_users",
        "admin_action_log",
        "users",
        ["admin_id"],
        ["id"],
    )
    # target_id полиморфный (user/ticket), поэтому FK нет — только индекс
    # для быстрого поиска действий по объекту.
    op.create_index(
        "ix_admin_action_log_target_id",
        "admin_action_log",
        ["target_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_action_log_target_id", table_name="admin_action_log")
    op.drop_constraint(
        "fk_admin_action_log_admin_id_users",
        "admin_action_log",
        type_="foreignkey",
    )
