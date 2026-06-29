"""
Tests for rate limiting middleware — using Redis mock.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.common.ratelimit import RateLimitMiddleware


class TestRateLimit:
    """Тесты rate limit с замоканным Redis."""

    @pytest.mark.asyncio
    async def test_under_limit(self):
        # Redis mock with all methods used by _check_limit
        redis_mock = AsyncMock()
        redis_mock.zremrangebyscore = AsyncMock()
        redis_mock.zadd = AsyncMock()
        redis_mock.expire = AsyncMock()
        redis_mock.zcard = AsyncMock(return_value=1)  # 1 request → under limit of 30

        req = AsyncMock()
        req.client.host = "127.0.0.1"
        req.url.path = "/api/v1/tickets"
        req.method = "GET"

        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        with patch("src.common.ratelimit.get_redis", AsyncMock(return_value=redis_mock)):
            middleware = RateLimitMiddleware(app=AsyncMock())
            result = await middleware.dispatch(request=req, call_next=call_next)

        assert result is not None
        assert result.status_code == 200
