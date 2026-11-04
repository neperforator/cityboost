"""
Security middleware для защиты заголовков ответов.

Добавляет стандартные security-заголовки (Helmet-like)
ко всем ответам API.
"""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware, добавляющий security-заголовки к каждому ответу:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - X-XSS-Protection: 0 (отключаем устаревший режим)
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: ограничиваем чувствительные API
      - Strict-Transport-Security: включаем HSTS
      - Content-Security-Policy: базовая защита от XSS
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # HSTS только если не DEBUG
        if not getattr(request.app.state, "debug", True):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Ответы аутентификации содержат токены/чувствительные данные.
        if request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"

        # Content-Security-Policy для API (не для статики)
        # Статика frontend'а управляется nginx
        if request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; frame-ancestors 'none'"
            )

        return response
