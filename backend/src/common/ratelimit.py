"""
Rate limiting middleware на основе Redis.

Простой sliding window счётчик для ключевых эндпоинтов.
Использует существующий Redis (через arq/redis-py).
"""

from __future__ import annotations

import logging
import time

import redis.asyncio as aioredis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config import settings

logger = logging.getLogger("cityboost.ratelimit")

# Лимиты: (путь_префикс, макс_запросов, окно_секунд)
RATE_LIMITS: list[tuple[str, int, int]] = [
    ("/api/v1/auth/register", 3, 3600),        # 3 регистрации в час
    ("/api/v1/auth/login", 10, 60),             # 10 попыток входа в минуту
    ("/api/v1/tickets", 30, 60),                # 30 запросов к заявкам в минуту
]

# IP-based блокировка после N неудачных попыток
BRUTE_FORCE_LIMIT = 5       # попыток
BRUTE_FORCE_WINDOW = 300     # 5 минут
BRUTE_FORCE_BAN = 900        # бан на 15 минут

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create Redis connection."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware rate limiting через Redis."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Проверяем только API-запросы
        if not path.startswith("/api/"):
            return await call_next(request)

        r = None
        try:
            r = await get_redis()
        except Exception:
            pass  # Redis недоступен — пропускаем проверку

        if r is not None:
            # Проверка по конкретным лимитам
            for prefix, max_req, window in RATE_LIMITS:
                if path.startswith(prefix):
                    key = f"ratelimit:{prefix}:{client_ip}"
                    allowed = await self._check_limit(r, key, max_req, window)
                    if not allowed:
                        logger.warning("Rate limit exceeded: %s from %s", path, client_ip)
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "Слишком много запросов. Попробуйте позже.",
                                "code": "RATE_LIMIT",
                            },
                        )
                    break

            # Brute-force защита для логина
            if path.startswith("/api/v1/auth/login"):
                ban_key = f"bruteforce:ban:{client_ip}"
                banned = await r.get(ban_key)
                if banned:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Слишком много попыток входа. Попробуйте через 15 минут.",
                            "code": "BRUTE_FORCE_BLOCK",
                        },
                    )

        response = await call_next(request)

        # Считаем неудачные попытки логина
        if r is not None and path.startswith("/api/v1/auth/login") and response.status_code == 401:
            attempts_key = f"bruteforce:attempts:{client_ip}"
            count = await r.incr(attempts_key)
            if count == 1:
                await r.expire(attempts_key, BRUTE_FORCE_WINDOW)
            if count >= BRUTE_FORCE_LIMIT:
                ban_key = f"bruteforce:ban:{client_ip}"
                await r.setex(ban_key, BRUTE_FORCE_BAN, "1")
                await r.delete(attempts_key)
                logger.warning("Brute force detected from %s - banned for %ds", client_ip, BRUTE_FORCE_BAN)

        return response

    async def _check_limit(
        self, r: aioredis.Redis, key: str, max_req: int, window: int
    ) -> bool:
        """Sliding window check."""
        now = time.time()
        window_start = now - window

        # Удаляем старые записи и добавляем текущую
        await r.zremrangebyscore(key, 0, window_start)
        await r.zadd(key, {str(now): now})
        await r.expire(key, window)

        count = await r.zcard(key)
        return count <= max_req
