"""
Tests for auth endpoints: register, login, JWT, profile, ban.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


async def _verify_user(db_session: AsyncSession, email: str) -> None:
    """Тесты не проверяют email-подтверждение — отмечаем пользователя verified."""
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_verified = True
    await db_session.flush()


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        payload = {"name": "Test User", "email": "test@example.com", "password": "StrongPass1"}
        r = await client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"name": "User", "email": "dup@example.com", "password": "StrongPass1"}
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        r2 = await client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        payload = {"name": "User", "email": "weak@example.com", "password": "123"}
        r = await client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        # Сначала регистрация
        reg = await client.post("/api/v1/auth/register", json={
            "name": "Login User", "email": "login@example.com", "password": "StrongPass1",
        })
        assert reg.status_code == 201
        await _verify_user(db_session, "login@example.com")
        r = await client.post("/api/v1/auth/login", json={
            "email": "login@example.com", "password": "StrongPass1",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        reg = await client.post("/api/v1/auth/register", json={
            "name": "WrongPass", "email": "wrong@example.com", "password": "StrongPass1",
        })
        assert reg.status_code == 201
        r = await client.post("/api/v1/auth/login", json={
            "email": "wrong@example.com", "password": "WrongPass1",
        })
        assert r.status_code == 401

    async def test_login_nonexistent_email(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/login", json={
            "email": "noone@example.com", "password": "StrongPass1",
        })
        assert r.status_code == 401

    async def test_login_accepts_special_use_domain(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        # Демо-аккаунты создаются на домене .local — вход должен их находить,
        # даже если строгая валидация EmailStr такой домен не пропускает.
        from src.auth.models import UserRole
        from src.auth.service import AuthService

        user = User(
            name="Demo User",
            email="demo.login@cityboost.local",
            password_hash=AuthService.hash_password("DemoPass123"),
            role=UserRole.USER,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        r = await client.post("/api/v1/auth/login", json={
            "email": "demo.login@cityboost.local", "password": "DemoPass123",
        })
        assert r.status_code == 200, r.text
        assert r.json()["access_token"]


class TestProfile:
    async def test_get_me(self, client: AsyncClient, db_session: AsyncSession):
        # Регистрируемся, подтверждаем email, логинимся и получаем токен
        reg = await client.post("/api/v1/auth/register", json={
            "name": "Me", "email": "me@example.com", "password": "StrongPass1",
        })
        assert reg.status_code == 201
        await _verify_user(db_session, "me@example.com")
        login_r = await client.post("/api/v1/auth/login", json={
            "email": "me@example.com", "password": "StrongPass1",
        })
        token = login_r.json()["access_token"]

        r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "me@example.com"
        assert data["name"] == "Me"

    async def test_get_me_unauthorized(self, client: AsyncClient):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401
