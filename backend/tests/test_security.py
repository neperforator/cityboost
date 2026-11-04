"""Регрессионные тесты для исправленных проблем безопасности."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.service import AuthService
from src.config import settings

pytestmark = pytest.mark.asyncio

PASSWORD = "StrongPass1"


async def _register(client: AsyncClient, email: str) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Security User", "email": email, "password": PASSWORD},
    )
    assert r.status_code == 201, r.text


async def _verify_user(db_session: AsyncSession, email: str) -> None:
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_verified = True
    await db_session.flush()


async def _login(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


class TestVerifyEmailBypass:
    async def test_verified_user_cannot_get_tokens_with_any_code(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Подтверждённый пользователь не должен получать токен по произвольному коду."""
        await _register(client, "verified@test.com")
        await _verify_user(db_session, "verified@test.com")

        r = await client.post(
            "/api/v1/auth/verify-email",
            json={"email": "verified@test.com", "code": "123456"},
        )

        assert r.status_code == 400
        assert "access_token" not in r.json()

    async def test_wrong_code_is_rejected_and_attempts_persist(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Неверный код не подтверждает email, а счётчик попыток сохраняется."""
        with patch.object(
            AuthService,
            "_generate_verification_code",
            return_value="654321",
        ):
            await _register(client, "attempts@test.com")

        for _ in range(settings.VERIFICATION_MAX_ATTEMPTS):
            r = await client.post(
                "/api/v1/auth/verify-email",
                json={"email": "attempts@test.com", "code": "000000"},
            )
            assert r.status_code == 400

        # Код заблокирован даже при вводе правильного значения.
        r = await client.post(
            "/api/v1/auth/verify-email",
            json={"email": "attempts@test.com", "code": "654321"},
        )
        assert r.status_code == 400

        result = await db_session.execute(
            select(User).where(User.email == "attempts@test.com"),
        )
        user = result.scalar_one()
        assert user.is_verified is False
        assert user.verification_code is None


class TestValidationLeak:
    async def test_password_not_returned_in_validation_error(self, client: AsyncClient):
        """422 не должен содержать введённый пароль ни в input, ни в тексте."""
        secret = "S3cret"
        r = await client.post(
            "/api/v1/auth/register",
            json={"name": "Leak", "email": "leak@test.com", "password": secret},
        )

        assert r.status_code == 422
        body = r.text
        assert secret not in body
        assert "input" not in r.json().get("details", [{}])[0]


class TestRefreshRotation:
    async def test_refresh_rotates_tokens_and_rejects_old_one(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        await _register(client, "rotate@test.com")
        await _verify_user(db_session, "rotate@test.com")

        access1 = await _login(client, "rotate@test.com")
        refresh1 = client.cookies.get("refresh_token")
        assert refresh1

        r = await client.post("/api/v1/auth/refresh")
        assert r.status_code == 200, r.text
        access2 = r.json()["access_token"]
        refresh2 = client.cookies.get("refresh_token")

        assert access1 != access2
        assert refresh1 != refresh2

        # Старый refresh-токен после ротации должен быть отвергнут.
        client.cookies.set("refresh_token", refresh1, path="/api/v1/auth")
        old = await client.post("/api/v1/auth/refresh")
        assert old.status_code == 401


class TestSessionRevocation:
    async def test_logout_invalidates_access_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        await _register(client, "logout@test.com")
        await _verify_user(db_session, "logout@test.com")

        token = await _login(client, "logout@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200

        logout = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout.status_code == 200

        # token_version изменился — старый access-токен больше не действует.
        after = await client.get("/api/v1/auth/me", headers=headers)
        assert after.status_code == 401
