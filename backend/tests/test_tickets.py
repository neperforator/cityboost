"""
Tests for ticket endpoints: CRUD, status changes, comments.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _register_and_login(client: AsyncClient, email: str = "user@test.com"):
    """Helper: register + login, return (token, user_id)."""
    await client.post("/api/v1/auth/register", json={
        "name": "Ticket User", "email": email, "password": "StrongPass1",
    })
    login_r = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "StrongPass1",
    })
    token = login_r.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


class TestTicketCRUD:
    async def test_create_ticket(self, client: AsyncClient):
        token, _ = await _register_and_login(client, "create@test.com")
        r = await client.post(
            "/api/v1/tickets",
            json={
                "title": "Test Ticket",
                "description": "Test description",
                "address": "ул. Ленина, 1",
                "category": "roads",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["title"] == "Test Ticket"
        assert data["status"] == "NEW"

    async def test_list_user_tickets(self, client: AsyncClient):
        token, _ = await _register_and_login(client, "list@test.com")
        await client.post(
            "/api/v1/tickets",
            json={"title": "T1", "description": "D1", "address": "A1", "category": "roads"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/tickets",
            json={"title": "T2", "description": "D2", "address": "A2", "category": "parks"},
            headers={"Authorization": f"Bearer {token}"},
        )
        r = await client.get("/api/v1/tickets", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 2
