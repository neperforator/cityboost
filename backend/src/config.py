"""
Конфигурация приложения CityBoost.
Все настройки загружаются из переменных окружения через pydantic-settings.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Основные настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- PostgreSQL ---
    DATABASE_URL: str = "postgresql+asyncpg://cityboost:cityboost_secret@db:5432/cityboost"

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- JWT ---
    JWT_SECRET_KEY: str = "change-this-to-a-very-long-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "cityboost"
    JWT_AUDIENCE: str = "cityboost-api"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        """Разрешаем только явно поддерживаемые алгоритмы подписи."""
        # Приложение использует симметричный секрет, поэтому только HMAC.
        allowed = {"HS256", "HS384", "HS512"}
        if value not in allowed:
            raise ValueError(f"JWT_ALGORITHM должен быть одним из: {sorted(allowed)}")
        return value

    # --- App ---
    APP_NAME: str = "CityBoost"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173"
    SQL_ECHO: bool = False
    # Доверять ли X-Forwarded-For (только если backend за доверенным reverse-proxy).
    TRUST_PROXY_HEADERS: bool = False

    # --- API Docs (Swagger/ReDoc) ---
    # Отдельно от DEBUG: можно включить документацию, даже когда DEBUG=false
    ENABLE_DOCS: bool = False

    @property
    def DOCS_ENABLED(self) -> bool:
        return self.ENABLE_DOCS or self.DEBUG

    @property
    def cors_origins(self) -> list[str]:
        """Список разрешённых Origin'ов (без wildcard при credentials)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- Storage / Files ---
    UPLOAD_DIR: str = "storage/uploads/tickets"
    MAX_FILE_SIZE_MB: int = 5
    MAX_FILES_PER_TICKET: int = 5

    # --- SMTP / Email ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@cityboost.ru"
    SMTP_USE_TLS: bool = True

    @property
    def SMTP_ENABLED(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER)

    # --- Frontend ---
    FRONTEND_URL: str = "http://localhost:5173"

    # --- Email verification ---
    VERIFICATION_CODE_TTL_MINUTES: int = 10
    VERIFICATION_MAX_ATTEMPTS: int = 10
    VERIFICATION_RESEND_COOLDOWN_SECONDS: int = 60

    # --- Admin 2FA (код на email) ---
    ADMIN_2FA_ENABLED: bool = True
    ADMIN_2FA_CODE_TTL_MINUTES: int = 10
    ADMIN_2FA_CHALLENGE_TTL_MINUTES: int = 10
    ADMIN_2FA_MAX_ATTEMPTS: int = 5
    ADMIN_2FA_RESEND_COOLDOWN_SECONDS: int = 60

    # --- Refresh Cookie ---
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"
    # Явная настройка: true для HTTPS, false для локального http.
    # Если не задана — вычисляется из DEBUG (для обратной совместимости).
    REFRESH_COOKIE_SECURE: bool | None = None

    @property
    def refresh_cookie_secure(self) -> bool:
        if self.REFRESH_COOKIE_SECURE is not None:
            return self.REFRESH_COOKIE_SECURE
        return not self.DEBUG

    # --- Sentry ---
    SENTRY_DSN: str = ""

    # --- Geocoding ---
    GEOCODING_API_URL: str = "https://nominatim.openstreetmap.org"
    GEOCODING_TIMEOUT_SECONDS: int = 2

    @property
    def UPLOAD_PATH(self) -> Path:
        """Абсолютный путь к директории загрузки файлов."""
        return Path(self.UPLOAD_DIR).resolve()

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def ALLOWED_MIME_TYPES(self) -> set[str]:
        return {"image/jpeg", "image/png"}


settings = Settings()
