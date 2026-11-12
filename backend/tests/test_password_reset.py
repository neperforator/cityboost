"""
Tests for password reset: forgot-password -> reset-password -> login.
"""

from __future__ import annotations

from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


async def _register(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str,
    password: str = "StrongPass1",
) -> User:
    """Зарегистрировать подтверждённого пользователя."""
    r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Reset User", "email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_verified = True
    await db_session.flush()
    return user


async def _request_reset(client: AsyncClient, email: str) -> str:
    """Запросить сброс и вернуть токен, который ушёл бы в письме."""
    captured: dict[str, str] = {}

    async def fake_send(self, email: str, token: str, name: str, base_url: str = "") -> bool:
        captured["token"] = token
        return True

    with patch("src.notifications.email.EmailService.send_password_reset", fake_send):
        r = await client.post("/api/v1/auth/forgot-password", json={"email": email})

    assert r.status_code == 200, r.text
    assert "token" in captured
    return captured["token"]


class TestPasswordReset:
    async def test_full_flow(self, client: AsyncClient, db_session: AsyncSession):
        await _register(client, db_session, "reset@example.com")
        token = await _request_reset(client, "reset@example.com")

        r = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "password": "NewStrongPass1"},
        )
        assert r.status_code == 200, r.text

        # Старый пароль больше не подходит.
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "StrongPass1"},
        )
        assert r.status_code == 401, r.text

        # Новый пароль работает.
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "NewStrongPass1"},
        )
        assert r.status_code == 200, r.text

    async def test_unknown_email_returns_200(self, client: AsyncClient):
        """Не раскрываем, зарегистрирован ли email."""
        r = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )
        assert r.status_code == 200, r.text

    async def test_invalid_token(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "not-a-real-token", "password": "NewStrongPass1"},
        )
        assert r.status_code == 400, r.text

    async def test_token_is_single_use(self, client: AsyncClient, db_session: AsyncSession):
        await _register(client, db_session, "single@example.com")
        token = await _request_reset(client, "single@example.com")

        payload = {"token": token, "password": "NewStrongPass1"}
        r = await client.post("/api/v1/auth/reset-password", json=payload)
        assert r.status_code == 200, r.text

        # Повторное использование того же токена должно отклоняться.
        r = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "password": "AnotherPass1"},
        )
        assert r.status_code == 400, r.text

    async def test_weak_password_rejected(self, client: AsyncClient, db_session: AsyncSession):
        await _register(client, db_session, "weakreset@example.com")
        token = await _request_reset(client, "weakreset@example.com")

        r = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "password": "short"},
        )
        assert r.status_code == 422, r.text
