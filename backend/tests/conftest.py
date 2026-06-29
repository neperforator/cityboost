"""
Pytest fixtures for CityBoost async tests.

Использует SQLite in-memory для тестов (не требуется PostgreSQL).
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

# Игнорируем интеграционный тест (не pytest-файл, а скрипт с последовательным вызовом)
collect_ignore = ["integration_test.py"]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def async_engine():
    """Create an in-memory SQLite engine for isolated tests."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh session scoped to a single test function."""
    session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(
    async_engine,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with overridden DB session and mocked Redis."""
    from src.main import app  # noqa: F811

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)

    with patch("src.common.ratelimit.get_redis", AsyncMock(return_value=None)):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
