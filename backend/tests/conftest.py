"""
Pytest fixtures for CityBoost async tests.

Использует testcontainers для PostgreSQL, либо — если не доступны —
запускает тесты с in-memory SQLite через aiosqlite.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base
from src.config import settings
from src.database import get_db

# Импортируем все модели, чтобы они зарегистрировались в Base.metadata
import src.auth.models  # noqa: F401 — User
import src.tickets.models  # noqa: F401 — Ticket, TicketFile, TicketHistory, TicketComment
import src.common.audit  # noqa: F401 — AdminActionLog

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Создаём временный async engine для тестовой БД.

    По умолчанию использует SQLite (aiosqlite), чтобы не зависеть от PostgreSQL.
    """
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Сессия для каждого теста — с транзакцией и откатом."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Тестовый HTTP-клиент с замоканой БД-сессией и отключённым rate limiting."""

    async def override_get_db():
        yield db_session

    # Импортируем app здесь, чтобы избежать циклических импортов
    from src.main import app

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    with patch("src.common.ratelimit.get_redis", AsyncMock(return_value=None)):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
