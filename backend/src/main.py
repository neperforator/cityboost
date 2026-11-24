"""
Главный модуль приложения CityBoost.

Собирает вместе все компоненты: роуты, middleware, обработчики ошибок.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.auth.admin import admin_user_router
from src.auth.router import auth_router
from src.common.audit_router import admin_audit_router
from src.common.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.common.middlewares import RequestLoggingMiddleware
from src.common.ratelimit import RateLimitMiddleware
from src.common.security import SecurityHeadersMiddleware
from src.config import settings
from src.tickets.admin import admin_router
from src.tickets.admin_dashboard import admin_dashboard_router
from src.tickets.analytics import analytics_router
from src.tickets.router import tickets_router

# ---------------------------------------------------------------------------
# Настройка логирования
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("cityboost")

# ---------------------------------------------------------------------------
# Fail-fast проверки production-конфигурации
# ---------------------------------------------------------------------------

_DEFAULT_JWT_SECRET = "change-this-to-a-very-long-random-secret-key"

if not settings.DEBUG:
    if settings.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET or len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY не настроен: задайте случайный секрет длиной не менее 32 символов",
        )
    if "*" in settings.cors_origins:
        raise RuntimeError(
            "CORS_ORIGINS не может содержать '*' в production: укажите явные Origin'ы",
        )
    if settings.DEBUG_BYPASS_EMAIL_AUTH:
        raise RuntimeError(
            "DEBUG_BYPASS_EMAIL_AUTH допустим только при DEBUG=true",
        )

# ---------------------------------------------------------------------------
# Создание FastAPI приложения
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API для городских заявок CityBoost — модульный монолит на FastAPI",
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    # FastAPI по умолчанию всегда отдаёт схему. Закрываем и её, иначе
    # /openapi.json остаётся доступным даже при выключенных docs.
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)

app.state.debug = settings.DEBUG

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

origins = settings.cors_origins
allow_credentials = True
if "*" in origins:
    # Браузер не разрешает credentials вместе с wildcard.
    allow_credentials = False

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

app.add_middleware(SecurityHeadersMiddleware)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

app.add_middleware(RateLimitMiddleware)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(RequestLoggingMiddleware)

# CORS добавляем последним: Starlette выполняет middleware в обратном порядке,
# поэтому CORS станет внешним и добавит заголовки даже к 429/500 от других
# middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ---------------------------------------------------------------------------
# Обработчики исключений
# ---------------------------------------------------------------------------

app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]

# Регистрируем стандартные обработчики
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def healthcheck() -> JSONResponse:
    """Проверка состояния сервиса."""
    return JSONResponse(content={"status": "ok", "app": settings.APP_NAME})


# ---------------------------------------------------------------------------
# Подключение роутов
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(admin_router)
app.include_router(admin_dashboard_router)
app.include_router(analytics_router)
app.include_router(admin_user_router)
app.include_router(admin_audit_router)


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
