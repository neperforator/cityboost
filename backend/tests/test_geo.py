"""
Tests for geocoding — using mocked HTTP client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.geo.service import GeoClient


class TestGeoClient:
    """Тесты геокодера с замоканными HTTP-запросами."""

    @pytest.mark.asyncio
    async def test_direct_geocode_success(self):
        mock_response = [
            {"lat": "55.7558", "lon": "37.6173", "display_name": "Moscow, Russia"},
        ]

        # Create a response mock — httpx Response has sync .json() and .raise_for_status()
        response_mock = MagicMock()
        response_mock.json.return_value = mock_response
        response_mock.status_code = 200

        # mock_session.get is an async call that returns the response
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=response_mock)

        with patch("src.geo.service.AsyncClient", return_value=mock_session):
            client = GeoClient()
            result = await client.direct_geocode("Moscow")

        assert result is not None
        assert result.latitude == 55.7558
        assert result.longitude == 37.6173

    @pytest.mark.asyncio
    async def test_direct_geocode_empty_results(self):
        response_mock = MagicMock()
        response_mock.json.return_value = []
        response_mock.status_code = 200

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=response_mock)

        with patch("src.geo.service.AsyncClient", return_value=mock_session):
            client = GeoClient()
            result = await client.direct_geocode("Nowhere")
            assert result is None
