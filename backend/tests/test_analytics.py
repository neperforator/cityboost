"""Тесты админской аналитики по заявкам."""

from __future__ import annotations

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
    """Создать подтверждённого пользователя напрямую в БД."""
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


def _access_token(user: User) -> str:
    """Выпустить access-токен без прохождения 2FA."""
    return AuthService.create_access_token(
        {"sub": str(user.id)},
        token_version=user.token_version,
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_access_token(user)}"}


async def _create_ticket(
    db_session: AsyncSession,
    user: User,
    *,
    status: TicketStatus = TicketStatus.NEW,
    assigned_to: User | None = None,
    title: str = "Заявка",
) -> Ticket:
    ticket = Ticket(
        user_id=user.id,
        assigned_to=assigned_to.id if assigned_to else None,
        title=title,
        description="Описание",
        status=status,
    )
    db_session.add(ticket)
    await db_session.flush()
    return ticket


class TestAnalytics:
    async def test_requires_admin(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        user = await _create_user(db_session, email="plain@test.com")

        forbidden = await client.get(
            "/api/v1/admin/analytics",
            headers=_auth(user),
        )
        assert forbidden.status_code == 403, forbidden.text

        unauthorized = await client.get("/api/v1/admin/analytics")
        assert unauthorized.status_code == 401

    async def test_returns_expected_structure(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session,
            email="analytics-admin@test.com",
            role=UserRole.ADMIN,
            name="Админ",
        )
        author = await _create_user(db_session, email="analytics-user@test.com")

        await _create_ticket(db_session, author, status=TicketStatus.NEW)
        await _create_ticket(
            db_session,
            author,
            status=TicketStatus.IN_WORK,
            assigned_to=admin,
        )
        await _create_ticket(
            db_session,
            author,
            status=TicketStatus.DONE,
            assigned_to=admin,
        )
        await _create_ticket(
            db_session,
            author,
            status=TicketStatus.CLOSED,
            assigned_to=admin,
        )

        response = await client.get(
            "/api/v1/admin/analytics?days=7",
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        data = response.json()

        assert data["period_days"] == 7
        assert len(data["by_day"]) == 7
        assert [point["status"] for point in data["by_status"]] == [
            "NEW",
            "IN_WORK",
            "DONE",
            "CLOSED",
        ]

        summary = data["summary"]
        assert summary["created_in_period"] == 4
        assert summary["resolved_in_period"] == 1
        assert summary["resolved_from_period"] == 1
        assert summary["open_now"] == 2
        assert summary["overdue_now"] == 0
        assert summary["backlog_start"] == 0
        assert summary["backlog_end"] == 2
        assert summary["resolution_rate"] == 25.0
        assert summary["avg_resolution_hours"] is not None
        assert summary["median_resolution_hours"] is not None
        assert summary["created_delta_pct"] is None
        assert summary["resolved_delta_pct"] is None

        # Статусы считаются только по заявкам, созданным за период.
        assert all(point["count"] == 1 for point in data["by_status"])
        assert all(point["percent"] == 25.0 for point in data["by_status"])

        assert len(data["by_assignee"]) == 1
        assert data["assignees_total"] == 1
        assignee = data["by_assignee"][0]
        assert assignee["admin_id"] == str(admin.id)
        assert assignee["name"] == "Админ"
        assert assignee["created_in_period"] == 3
        assert assignee["resolved_in_period"] == 1
        assert assignee["open_now"] == 1
        assert assignee["overdue"] == 0
        assert assignee["avg_resolution_hours"] is not None

        # Дневные точки отсортированы, очередь накапливается.
        dates = [point["date"] for point in data["by_day"]]
        assert dates == sorted(dates)
        assert data["by_day"][-1]["backlog"] == 2

    async def test_limits_assignee_list(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Список исполнителей ограничен, но их общее число сохраняется."""
        admin = await _create_user(
            db_session,
            email="analytics-admin3@test.com",
            role=UserRole.ADMIN,
            name="Главный админ",
        )
        author = await _create_user(db_session, email="analytics-user3@test.com")

        for index in range(12):
            assignee = await _create_user(
                db_session,
                email=f"assignee{index}@test.com",
                role=UserRole.ADMIN,
                name=f"Исполнитель {index}",
            )
            await _create_ticket(
                db_session,
                author,
                status=TicketStatus.DONE,
                assigned_to=assignee,
            )

        response = await client.get(
            "/api/v1/admin/analytics?days=7",
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["assignees_total"] == 12
        assert len(data["by_assignee"]) == 10

    async def test_rejects_invalid_period(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session,
            email="analytics-admin2@test.com",
            role=UserRole.ADMIN,
        )

        response = await client.get(
            "/api/v1/admin/analytics?days=0",
            headers=_auth(admin),
        )
        assert response.status_code == 422
