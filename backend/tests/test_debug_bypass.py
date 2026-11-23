"""
Tests for DEBUG_BYPASS_EMAIL_AUTH: регистрация и вход без писем в DEBUG.

Флаг действует только при DEBUG=true; в production backend не стартует
(проверка в src/main.py), а свойство settings.email_auth_bypassed его гасит.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.service import AuthService
from src.config import settings


@pytest.fixture
def bypass_email_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Включить обход подтверждения email только на время теста."""
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "DEBUG_BYPASS_EMAIL_AUTH", True)


def test_bypass_requires_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "DEBUG_BYPASS_EMAIL_AUTH", True)
    assert settings.email_auth_bypassed is False


class TestDebugBypass:
    async def test_register_returns_verified_user(
        self,
        client: AsyncClient,
        bypass_email_auth: None,
    ):
        r = await client.post("/api/v1/auth/register", json={
            "name": "Bypass User",
            "email": "bypass@example.com",
            "password": "StrongPass1",
        })
        assert r.status_code == 201, r.text
        assert r.json()["is_verified"] is True

    async def test_login_without_email_confirmation(
        self,
        client: AsyncClient,
        bypass_email_auth: None,
    ):
        await client.post("/api/v1/auth/register", json={
            "name": "Bypass User",
            "email": "bypass.login@example.com",
            "password": "StrongPass1",
        })
        r = await client.post("/api/v1/auth/login", json={
            "email": "bypass.login@example.com",
            "password": "StrongPass1",
        })
        assert r.status_code == 200, r.text
        assert r.json()["access_token"]

    async def test_refresh_works_for_unverified_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        bypass_email_auth: None,
    ):
        # Пользователь создан в обход регистрации: почта не подтверждена.
        user = User(
            name="Unverified",
            email="unverified@example.com",
            password_hash=AuthService.hash_password("StrongPass1"),
            role=UserRole.USER,
            is_verified=False,
        )
        db_session.add(user)
        await db_session.flush()

        login_r = await client.post("/api/v1/auth/login", json={
            "email": "unverified@example.com",
            "password": "StrongPass1",
        })
        assert login_r.status_code == 200, login_r.text

        refresh_r = await client.post("/api/v1/auth/refresh", json={})
        assert refresh_r.status_code == 200, refresh_r.text
        assert refresh_r.json()["access_token"]

    async def test_admin_login_skips_2fa(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        bypass_email_auth: None,
    ):
        admin = User(
            name="Admin",
            email="bypass.admin@example.com",
            password_hash=AuthService.hash_password("StrongPass1"),
            role=UserRole.ADMIN,
            is_verified=False,
        )
        db_session.add(admin)
        await db_session.flush()

        r = await client.post("/api/v1/auth/login", json={
            "email": "bypass.admin@example.com",
            "password": "StrongPass1",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("requires_2fa") is not True
        assert data["access_token"]
