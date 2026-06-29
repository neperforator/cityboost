"""initial

Revision ID: 0001
Revises:
Create Date: 2026-06-28 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- enum types (IF NOT EXISTS для идемпотентности) ---
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('USER', 'ADMIN');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_status') THEN
                CREATE TYPE ticket_status AS ENUM ('NEW', 'IN_WORK', 'DONE', 'CLOSED');
            END IF;
        END $$;
    """))

    # --- users ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(150) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role user_role NOT NULL DEFAULT 'USER',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")

    # --- tickets ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id),
            assigned_to UUID REFERENCES users(id),
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            status ticket_status NOT NULL DEFAULT 'NEW',
            latitude FLOAT,
            longitude FLOAT,
            address VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_address ON tickets (address)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON tickets (created_at)")

    # --- ticket_files ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS ticket_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID NOT NULL REFERENCES tickets(id),
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # --- ticket_history ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS ticket_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID NOT NULL REFERENCES tickets(id),
            changed_by UUID NOT NULL REFERENCES users(id),
            old_status VARCHAR(20),
            new_status VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # --- ticket_comments ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS ticket_comments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID NOT NULL REFERENCES tickets(id),
            author_id UUID NOT NULL REFERENCES users(id),
            comment_text TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # --- alembic_version (чтобы не повторять миграцию) ---
    # alembic сам управляет этой таблицей, так что всё ок


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ticket_comments CASCADE")
    op.execute("DROP TABLE IF EXISTS ticket_history CASCADE")
    op.execute("DROP TABLE IF EXISTS ticket_files CASCADE")
    op.execute("DROP TABLE IF EXISTS tickets CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TYPE IF EXISTS ticket_status")
    op.execute("DROP TYPE IF EXISTS user_role")
