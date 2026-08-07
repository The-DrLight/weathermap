"""Fetches live and historical atmospheric data from Open-Meteo, defaulting to Lagos."""

import asyncio
from datetime import date, datetime, timezone
from typing import Any

import httpx

from app.core.config import settings

LIVE_RETRY_ATTEMPTS = 3
LIVE_RETRY_DELAY_SECONDS = 5
LIVE_CACHE_TTL_SECONDS = 60

# Cache keyed by (lat, lon) rounded to 4dp, mapping to (response, fetched_at).
_live_cache: dict[tuple[float, float], tuple[dict[str, Any], datetime]] = {}


def _cache_key(lat: float | None, lon: float | None) -> tuple[float, float]:
    return (
        round(lat if lat is not None else settings.lagos_lat, 4),
        round(lon if lon is not None else settings.lagos_lon, 4),
    )


def get_cached_live_weather(lat: float | None, lon: float | None) -> tuple[dict[str, Any], datetime] | None:
    """Return the last successful live weather response for these coordinates, if any."""
    return _live_cache.get(_cache_key(lat, lon))


def is_cache_fresh(fetched_at: datetime) -> bool:
    return (datetime.now(timezone.utc) - fetched_at).total_seconds() < LIVE_CACHE_TTL_SECONDS

CURRENT_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
]

DAILY_FIELDS = [
    "precipitation_sum",
    "precipitation_probability_max",
]

ARCHIVE_HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
]


async def fetch_live_weather(lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
    """Fetch current atmospheric readings plus today's forecast summary for the given coordinates."""
    params = {
        "latitude": lat if lat is not None else settings.lagos_lat,
        "longitude": lon if lon is not None else settings.lagos_lon,
        "current": ",".join(CURRENT_FIELDS),
        "daily": ",".join(DAILY_FIELDS),
        "timezone": "auto",
        "forecast_days": 2,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(1, LIVE_RETRY_ATTEMPTS + 1):
            response = await client.get(settings.open_meteo_base_url, params=params)
            if response.status_code == 429 and attempt < LIVE_RETRY_ATTEMPTS:
                await asyncio.sleep(LIVE_RETRY_DELAY_SECONDS)
                continue
            response.raise_for_status()
            data = response.json()
            _live_cache[_cache_key(lat, lon)] = (data, datetime.now(timezone.utc))
            return data


async def fetch_historical_weather(
    start_date: date, end_date: date, lat: float | None = None, lon: float | None = None
) -> dict[str, Any]:
    """Fetch hourly historical atmospheric data for the given coordinates."""
    params = {
        "latitude": lat if lat is not None else settings.lagos_lat,
        "longitude": lon if lon is not None else settings.lagos_lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": ",".join(ARCHIVE_HOURLY_FIELDS),
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(settings.open_meteo_archive_url, params=params)
        response.raise_for_status()
        return response.json()
