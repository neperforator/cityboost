"""Тесты массовых действий администратора с заявками."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.service import AuthService
from src.tickets.models import Ticket, TicketStatus

pytestmark = pytest.mark.asyncio

PASSWORD = "StrongPass1"


async def _create_user(
    db_session: AsyncSession,
    *,
    email: str,
    role: UserRole = UserRole.USER,
    name: str = "User",
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=AuthService.hash_password(PASSWORD),
        role=role,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def _auth(user: User) -> dict[str, str]:
    token = AuthService.create_access_token(
        {"sub": str(user.id)},
        token_version=user.token_version,
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_ticket(
    db_session: AsyncSession,
    author: User,
    *,
    title: str = "Заявка",
    status: TicketStatus = TicketStatus.NEW,
    assigned_to: User | None = None,
) -> Ticket:
    ticket = Ticket(
        user_id=author.id,
        title=title,
        description="Описание",
        status=status,
        assigned_to=assigned_to.id if assigned_to else None,
    )
    db_session.add(ticket)
    await db_session.flush()
    return ticket


class TestAdminBulkActions:
    async def test_bulk_status_updates_all(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session, email="bulk-admin@test.com", role=UserRole.ADMIN,
        )
        author = await _create_user(db_session, email="bulk-author@test.com")
        tickets = [
            await _create_ticket(db_session, author, title=f"Заявка {index}")
            for index in range(3)
        ]

        response = await client.patch(
            "/api/v1/admin/tickets/bulk/status",
            headers=_auth(admin),
            json={
                "ticket_ids": [str(ticket.id) for ticket in tickets],
                "new_status": "DONE",
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["updated"] == 3
        assert data["skipped"] == 0
        assert data["failed"] == 0
        for ticket in tickets:
            await db_session.refresh(ticket)
            assert ticket.status == TicketStatus.DONE

    async def test_bulk_status_skips_same_and_not_found(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session, email="bulk-admin2@test.com", role=UserRole.ADMIN,
        )
        author = await _create_user(db_session, email="bulk-author2@test.com")
        existing = await _create_ticket(
            db_session, author, status=TicketStatus.DONE,
        )
        missing_id = uuid.uuid4()

        response = await client.patch(
            "/api/v1/admin/tickets/bulk/status",
            headers=_auth(admin),
            json={
                "ticket_ids": [str(existing.id), str(missing_id)],
                "new_status": "DONE",
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["updated"] == 0
        assert data["skipped"] == 1
        assert data["failed"] == 1
        assert data["errors"][0]["ticket_id"] == str(missing_id)
        assert len(data["skipped_items"]) == 1
        skipped = data["skipped_items"][0]
        assert skipped["ticket_id"] == str(existing.id)
        assert skipped["title"] == existing.title
        assert "Уже в статусе" in skipped["reason"]

    async def test_bulk_status_closed_requires_reason(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session, email="bulk-admin3@test.com", role=UserRole.ADMIN,
        )
        author = await _create_user(db_session, email="bulk-author3@test.com")
        ticket = await _create_ticket(db_session, author)

        response = await client.patch(
            "/api/v1/admin/tickets/bulk/status",
            headers=_auth(admin),
            json={
                "ticket_ids": [str(ticket.id)],
                "new_status": "CLOSED",
            },
        )

        assert response.status_code == 422

    async def test_bulk_assign_moves_new_to_work_and_skips_done(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session, email="bulk-admin4@test.com", role=UserRole.ADMIN,
        )
        author = await _create_user(db_session, email="bulk-author4@test.com")
        new_ticket = await _create_ticket(db_session, author)
        done_ticket = await _create_ticket(
            db_session, author, status=TicketStatus.DONE,
        )

        response = await client.patch(
            "/api/v1/admin/tickets/bulk/assign",
            headers=_auth(admin),
            json={"ticket_ids": [str(new_ticket.id), str(done_ticket.id)]},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["updated"] == 1
        assert data["skipped"] == 1
        assert data["failed"] == 0
        assert data["skipped_items"][0]["reason"] == "Заявка уже выполнена"

        await db_session.refresh(new_ticket)
        await db_session.refresh(done_ticket)
        assert new_ticket.assigned_to == admin.id
        assert new_ticket.status == TicketStatus.IN_WORK
        assert done_ticket.assigned_to is None
        assert done_ticket.status == TicketStatus.DONE

    async def test_bulk_assign_explains_already_assigned(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session, email="bulk-admin6@test.com", role=UserRole.ADMIN,
        )
        author = await _create_user(db_session, email="bulk-author6@test.com")
        ticket = await _create_ticket(
            db_session,
            author,
            status=TicketStatus.IN_WORK,
            assigned_to=admin,
        )

        response = await client.patch(
            "/api/v1/admin/tickets/bulk/assign",
            headers=_auth(admin),
            json={"ticket_ids": [str(ticket.id)]},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["skipped"] == 1
        assert data["skipped_items"][0]["reason"] == "Уже назначена на вас"

    async def test_bulk_actions_require_admin(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        user = await _create_user(db_session, email="bulk-user@test.com")
        author = await _create_user(db_session, email="bulk-author5@test.com")
        ticket = await _create_ticket(db_session, author)

        response = await client.patch(
            "/api/v1/admin/tickets/bulk/status",
            headers=_auth(user),
            json={
                "ticket_ids": [str(ticket.id)],
                "new_status": "DONE",
            },
        )

        assert response.status_code == 403
