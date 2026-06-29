"""
Глобальные обработчики исключений и унифицированный формат ошибок.

Все ошибки приводятся к единому JSON-формату:
    {"error": "Сообщение об ошибке", "code": "VALIDATION_ERROR|NOT_FOUND|..."}
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("cityboost.exceptions")


ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "REQUEST_ENTITY_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Обработчик HTTP-исключений."""
    code = ERROR_CODES.get(exc.status_code, "UNKNOWN_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": code},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Обработчик ошибок валидации Pydantic."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    message = first_error.get("msg", "Ошибка валидации данных")

    logger.warning(
        "Validation error: %s | path: %s",
        errors,
        request.url.path,
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": message,
            "code": "VALIDATION_ERROR",
            "details": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Глобальный обработчик непредвиденных исключений (500)."""
    logger.exception(
        "Unhandled exception: %s | path: %s",
        str(exc),
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )
