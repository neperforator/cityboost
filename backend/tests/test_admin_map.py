"""Тесты админской карты заявок."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
    assigned_to: User | None = None,
    created_at: datetime | None = None,
) -> Ticket:
    values = {
        "user_id": author.id,
        "title": title,
        "description": "Описание",
        "status": status,
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "assigned_to": assigned_to.id if assigned_to else None,
    }
    if created_at is not None:
        values["created_at"] = created_at

    ticket = Ticket(**values)
    db_session.add(ticket)
    await db_session.flush()
    return ticket


class TestAdminMap:
    async def test_returns_only_geolocated_tickets(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session,
            email="map-admin@test.com",
            role=UserRole.ADMIN,
            name="Картограф",
        )
        author = await _create_user(db_session, email="map-author@test.com")

        point = await _create_ticket(
            db_session,
            author,
            title="Яма на дороге",
            status=TicketStatus.IN_WORK,
            latitude=55.1904,
            longitude=30.2049,
        )
        # Заявка без координат не должна попасть на карту.
        await _create_ticket(
            db_session,
            author,
            title="Без координат",
            status=TicketStatus.NEW,
        )
        # Заявка за пределами Витебска тоже не должна попасть на карту.
        await _create_ticket(
            db_session,
            author,
            title="Заявка из другого города",
            status=TicketStatus.NEW,
            latitude=55.75,
            longitude=37.62,
        )

        response = await client.get(
            "/api/v1/admin/tickets/map",
            headers=_auth(admin),
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 1
        assert data["limit"] == 1000
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["id"] == str(point.id)
        assert item["title"] == "Яма на дороге"
        assert item["status"] == "IN_WORK"
        assert item["latitude"] == 55.1904
        assert item["longitude"] == 30.2049
        assert item["address"] is None
        assert item["assigned_to_name"] is None

        # Фильтр по статусу.
        filtered = await client.get(
            "/api/v1/admin/tickets/map?status=NEW",
            headers=_auth(admin),
        )
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 0
        assert filtered.json()["items"] == []

        # Ограничение количества точек.
        limited = await client.get(
            "/api/v1/admin/tickets/map?limit=1",
            headers=_auth(admin),
        )
        assert limited.status_code == 200
        assert limited.json()["limit"] == 1
        assert len(limited.json()["items"]) == 1

    async def test_supports_list_filters(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_user(
            db_session,
            email="map-filter-admin@test.com",
            role=UserRole.ADMIN,
            name="Фильтров",
        )
        other_admin = await _create_user(
            db_session,
            email="map-filter-other@test.com",
            role=UserRole.ADMIN,
            name="Другой",
        )
        author = await _create_user(db_session, email="map-filter-author@test.com")
        now = datetime.now(UTC)

        await _create_ticket(
            db_session,
            author,
            title="Яма на дороге",
            status=TicketStatus.IN_WORK,
            latitude=55.1904,
            longitude=30.2049,
            address="ул. Ленина",
            assigned_to=admin,
            created_at=now,
        )
        await _create_ticket(
            db_session,
            author,
            title="Фонарь не горит",
            status=TicketStatus.NEW,
            latitude=55.1920,
            longitude=30.2080,
            address="ул. Мира",
            created_at=now,
        )
        await _create_ticket(
            db_session,
            author,
            title="Старая яма",
            status=TicketStatus.IN_WORK,
            latitude=55.1850,
            longitude=30.2100,
            address="ул. Садовая",
            assigned_to=other_admin,
            created_at=now - timedelta(days=20),
        )

        search = await client.get(
            "/api/v1/admin/tickets/map?q=Ленина",
            headers=_auth(admin),
        )
        assert search.status_code == 200, search.text
        assert search.json()["total"] == 1
        assert search.json()["items"][0]["title"] == "Яма на дороге"

        mine = await client.get(
            "/api/v1/admin/tickets/map?assignee=me",
            headers=_auth(admin),
        )
        assert mine.status_code == 200
        assert [item["title"] for item in mine.json()["items"]] == ["Яма на дороге"]

        unassigned = await client.get(
            "/api/v1/admin/tickets/map?assignee=unassigned",
            headers=_auth(admin),
        )
        assert unassigned.status_code == 200
        assert [item["title"] for item in unassigned.json()["items"]] == ["Фонарь не горит"]

        overdue = await client.get(
            "/api/v1/admin/tickets/map?overdue=true",
            headers=_auth(admin),
        )
        assert overdue.status_code == 200
        assert [item["title"] for item in overdue.json()["items"]] == ["Старая яма"]

    async def test_requires_admin(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        user = await _create_user(db_session, email="map-user@test.com")

        forbidden = await client.get(
            "/api/v1/admin/tickets/map",
            headers=_auth(user),
        )
        assert forbidden.status_code == 403

        unauthorized = await client.get("/api/v1/admin/tickets/map")
        assert unauthorized.status_code == 401
