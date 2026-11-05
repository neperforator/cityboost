"""
Tests for ticket endpoints: CRUD, status changes, comments.
"""

from __future__ import annotations

import struct
import zlib

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User

pytestmark = pytest.mark.asyncio


def _mini_png() -> bytes:
    """Создать минимальный валидный PNG (1×1, красный)."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        raw = chunk_type + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")  # filter=none, RGB(255,0,0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )


async def _register_and_login(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str = "user@test.com",
):
    """Helper: register + verify email + login, return (token, user_id)."""
    await client.post("/api/v1/auth/register", json={
        "name": "Ticket User", "email": email, "password": "StrongPass1",
    })
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_verified = True
    await db_session.flush()

    login_r = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "StrongPass1",
    })
    token = login_r.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


def _ticket_post_data() -> dict:
    """Вернуть multipart-data + files для POST /api/v1/tickets."""
    data = {
        "title": "Test Ticket",
        "description": "Test description",
        "address": "ул. Ленина, 1",
    }
    files = [("files", ("test.png", _mini_png(), "image/png"))]
    return data, files


class TestTicketCRUD:
    async def test_create_ticket(self, client: AsyncClient, db_session: AsyncSession):
        token, _ = await _register_and_login(client, db_session, "create@test.com")
        data, files = _ticket_post_data()
        r = await client.post(
            "/api/v1/tickets",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["title"] == "Test Ticket"
        assert data["status"] == "NEW"
        # Должен быть хотя бы один файл
        assert len(data.get("files", [])) >= 1

    async def test_create_ticket_with_vitebsk_coords(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        token, _ = await _register_and_login(client, db_session, "coords@test.com")
        data, files = _ticket_post_data()
        data = {**data, "latitude": "55.1904", "longitude": "30.2049"}
        r = await client.post(
            "/api/v1/tickets",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["latitude"] == pytest.approx(55.1904)
        assert body["longitude"] == pytest.approx(30.2049)

    async def test_create_ticket_accepts_vitebsk_outskirts(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        token, _ = await _register_and_login(client, db_session, "outskirts@test.com")
        data, files = _ticket_post_data()
        # Северо-западная окраина Витебска — должна приниматься.
        data = {**data, "latitude": "55.30", "longitude": "30.10"}
        r = await client.post(
            "/api/v1/tickets",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, r.text

    async def test_reject_coords_outside_vitebsk(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        token, _ = await _register_and_login(client, db_session, "moscow@test.com")
        data, files = _ticket_post_data()
        # Координаты Москвы — за пределами Витебска.
        data = {**data, "latitude": "55.75", "longitude": "37.62"}
        r = await client.post(
            "/api/v1/tickets",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400, r.text
        assert "Витебск" in r.json()["error"]

    async def test_reject_partial_coords(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        token, _ = await _register_and_login(client, db_session, "partial@test.com")
        data, files = _ticket_post_data()
        data = {**data, "latitude": "55.1904"}
        r = await client.post(
            "/api/v1/tickets",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400, r.text
        assert "вместе" in r.json()["error"]

    async def test_list_user_tickets(self, client: AsyncClient, db_session: AsyncSession):
        token, _ = await _register_and_login(client, db_session, "list@test.com")
        data1, files1 = _ticket_post_data()
        await client.post(
            "/api/v1/tickets",
            data=data1,
            files=files1,
            headers={"Authorization": f"Bearer {token}"},
        )
        data2, files2 = _ticket_post_data()
        await client.post(
            "/api/v1/tickets",
            data={**data2, "title": "T2", "description": "D2"},
            files=files2,
            headers={"Authorization": f"Bearer {token}"},
        )
        r = await client.get("/api/v1/tickets", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 2
