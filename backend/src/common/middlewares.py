"""
Middleware для логирования и обработки запросов.

- Генерирует уникальный X-Request-ID для каждого запроса.
- Логирует структурный JSON (method, path, status_code, processing_time).
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("cityboost.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware, который:
      1. Генерирует X-Request-ID, если его нет.
      2. Замеряет время обработки запроса.
      3. Логирует JSON-строку с метаданными запроса.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        setattr(request.state, "request_id", request_id)

        start_time = time.monotonic()

        response: Response = await call_next(request)

        processing_time = time.monotonic() - start_time

        response.headers["X-Request-ID"] = request_id

        # Структурное JSON-логирование в stdout
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_string": str(request.url.query) if request.url.query else "",
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "client_host": request.client.host if request.client else None,
        }

        if response.status_code >= 500:
            logger.error("Request processed", extra={"http": log_data})
        elif response.status_code >= 400:
            logger.warning("Request processed", extra={"http": log_data})
        else:
            logger.info("Request processed", extra={"http": log_data})

        return response
