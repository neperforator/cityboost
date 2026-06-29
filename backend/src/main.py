"""
Главный модуль приложения CityBoost.

Собирает вместе все компоненты: роуты, middleware, обработчики ошибок.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from src.tickets.router import tickets_router

# ---------------------------------------------------------------------------
# Sentry (только в production)
# ---------------------------------------------------------------------------

if not settings.DEBUG and settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment="production",
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
    logger.info("Sentry initialized (production mode)")

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
# Создание FastAPI приложения
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API для городских заявок CityBoost — модульный монолит на FastAPI",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.state.debug = settings.DEBUG

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

origins = (
    ["*"]
    if settings.CORS_ORIGINS == "*"
    else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ---------------------------------------------------------------------------
# Обработчики исключений
# ---------------------------------------------------------------------------

app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]

# Импортируем и регистрируем стандартные обработчики
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.exceptions import RequestValidationError

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
