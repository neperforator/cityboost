"""
Конфигурация приложения CityBoost.
Все настройки загружаются из переменных окружения через pydantic-settings.
"""

from __future__ import annotations

from pathlib import Path

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
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- App ---
    APP_NAME: str = "CityBoost"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "*"

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

    # --- Refresh Cookie ---
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"

    @property
    def REFRESH_COOKIE_SECURE(self) -> bool:
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
