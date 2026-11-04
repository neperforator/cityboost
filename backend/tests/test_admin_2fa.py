"""Tests for mandatory email 2FA for administrators."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.service import AuthService

pytestmark = pytest.mark.asyncio

PASSWORD = "StrongPass1"
CODE = "123456"


async def _create_admin(
    db_session: AsyncSession,
    email: str = "admin@test.com",
) -> User:
    """Создать подтверждённого администратора напрямую в БД."""
    user = User(
        name="Admin",
        email=email,
        password_hash=AuthService.hash_password(PASSWORD),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def _email_mock() -> AsyncMock:
    return AsyncMock(return_value=True)


async def _login(client: AsyncClient, email: str = "admin@test.com"):
    return await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )


class TestAdmin2FA:
    async def test_login_requires_2fa_and_no_tokens(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        await _create_admin(db_session)

        with (
            patch.object(
                AuthService,
                "_generate_two_factor_code",
                return_value=CODE,
            ),
            patch(
                "src.notifications.email.EmailService.send_admin_2fa_code",
                new=_email_mock(),
            ),
        ):
            r = await _login(client)

        assert r.status_code == 200, r.text
        data = r.json()
        assert data["requires_2fa"] is True
        assert data["challenge_token"]
        assert data.get("access_token") is None

        # Challenge-токен нельзя использовать как обычный access-токен.
        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['challenge_token']}"},
        )
        assert me.status_code == 401

    async def test_verify_code_issues_tokens(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        await _create_admin(db_session)

        with (
            patch.object(
                AuthService,
                "_generate_two_factor_code",
                return_value=CODE,
            ),
            patch(
                "src.notifications.email.EmailService.send_admin_2fa_code",
                new=_email_mock(),
            ),
        ):
            login = await _login(client)
            challenge = login.json()["challenge_token"]

            wrong = await client.post(
                "/api/v1/auth/admin-2fa/verify",
                json={"challenge_token": challenge, "code": "000000"},
            )
            assert wrong.status_code == 401

            ok = await client.post(
                "/api/v1/auth/admin-2fa/verify",
                json={"challenge_token": challenge, "code": CODE},
            )

        assert ok.status_code == 200, ok.text
        assert ok.json()["access_token"]
        assert client.cookies.get("refresh_token")

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {ok.json()['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["role"] == "admin"

        # Refresh после 2FA должен работать (в токене есть amr=2fa).
        refreshed = await client.post("/api/v1/auth/refresh")
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json()["access_token"]

    async def test_refresh_rejects_session_without_2fa(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin = await _create_admin(db_session)

        # Имитируем старую сессию: refresh-токен без amr=2fa.
        legacy_refresh = AuthService.create_raw_refresh_token(admin.id)
        admin.refresh_token_hash = AuthService.hash_refresh_token(legacy_refresh)
        await db_session.flush()

        client.cookies.set(
            "refresh_token",
            legacy_refresh,
            path="/api/v1/auth",
        )
        r = await client.post("/api/v1/auth/refresh")

        assert r.status_code == 401

    async def test_code_is_locked_after_max_attempts(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        await _create_admin(db_session)

        with (
            patch.object(
                AuthService,
                "_generate_two_factor_code",
                return_value=CODE,
            ),
            patch(
                "src.notifications.email.EmailService.send_admin_2fa_code",
                new=_email_mock(),
            ),
        ):
            login = await _login(client)
            challenge = login.json()["challenge_token"]

            for _ in range(5):
                r = await client.post(
                    "/api/v1/auth/admin-2fa/verify",
                    json={"challenge_token": challenge, "code": "000000"},
                )
                assert r.status_code == 401

            ok = await client.post(
                "/api/v1/auth/admin-2fa/verify",
                json={"challenge_token": challenge, "code": CODE},
            )

        assert ok.status_code == 401

    async def test_resend_has_cooldown(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        await _create_admin(db_session)

        with (
            patch.object(
                AuthService,
                "_generate_two_factor_code",
                return_value=CODE,
            ),
            patch(
                "src.notifications.email.EmailService.send_admin_2fa_code",
                new=_email_mock(),
            ),
        ):
            login = await _login(client)
            challenge = login.json()["challenge_token"]

            resend = await client.post(
                "/api/v1/auth/admin-2fa/resend",
                json={"challenge_token": challenge},
            )

        assert resend.status_code == 429
