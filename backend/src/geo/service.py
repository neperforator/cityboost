"""
Сервис геокодирования (прямой и обратный).
Использует Nominatim (OpenStreetMap) с возможностью замены на mock для тестов.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from httpx import AsyncClient, HTTPError, TimeoutException

from src.config import settings


@dataclass
class GeoResult:
    """Результат геокодирования."""
    latitude: float
    longitude: float
    address: str | None = None
    display_name: str | None = None


class GeoClient:
    """
    HTTP-клиент для геокодирования через Nominatim API.

    Легко заменяется mock-объектом при тестировании.
    """

    BASE_URL = settings.GEOCODING_API_URL.rstrip("/")
    TIMEOUT = settings.GEOCODING_TIMEOUT_SECONDS

    def __init__(self, client: AsyncClient | None = None):
        """
        Args:
            client: Передайте заранее сконфигурированный AsyncClient (например, mock).
        """
        self._client = client or AsyncClient(
            timeout=self.TIMEOUT,
            headers={"User-Agent": f"{settings.APP_NAME}/1.0"},
        )

    async def reverse_geocode(self, lat: float, lon: float) -> GeoResult | None:
        """
        Обратное геокодирование: координаты → адрес.

        Выполняется с таймаутом settings.GEOCODING_TIMEOUT_SECONDS секунд.
        Возвращает None при ошибке или таймауте.
        """
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                return None
            return GeoResult(
                latitude=lat,
                longitude=lon,
                address=data.get("display_name"),
                display_name=data.get("display_name"),
            )
        except (TimeoutException, HTTPError, ValueError):
            return None

    async def direct_geocode(self, address: str) -> GeoResult | None:
        """
        Прямое геокодирование: адрес → координаты.

        Выполняется с таймаутом settings.GEOCODING_TIMEOUT_SECONDS секунд.
        Возвращает None при ошибке или таймауте.
        """
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return GeoResult(
                latitude=float(data[0]["lat"]),
                longitude=float(data[0]["lon"]),
                address=address,
                display_name=data[0].get("display_name"),
            )
        except (TimeoutException, HTTPError, ValueError, KeyError, IndexError):
            return None

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        if self._client:
            await self._client.aclose()


# Экземпляр по умолчанию
default_geo_client = GeoClient()


async def resolve_address(lat: float, lon: float) -> str | None:
    """
    Получить адрес по координатам (обратное геокодирование).

    Если сервис недоступен — возвращает None (фоновый таск выполнит повторно).
    """
    result = await default_geo_client.reverse_geocode(lat, lon)
    return result.address if result else None


async def resolve_coordinates(address: str) -> tuple[float | None, float | None]:
    """
    Получить координаты по адресу (прямое геокодирование).

    Если сервис недоступен — возвращает (None, None).
    """
    result = await default_geo_client.direct_geocode(address)
    if result:
        return result.latitude, result.longitude
    return None, None
