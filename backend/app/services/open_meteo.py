"""Fetches live and historical atmospheric data for Lagos from Open-Meteo."""

from datetime import date
from typing import Any

import httpx

from app.core.config import settings

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


async def fetch_live_weather() -> dict[str, Any]:
    """Fetch current Lagos atmospheric readings plus today's forecast summary."""
    params = {
        "latitude": settings.lat,
        "longitude": settings.lon,
        "current": ",".join(CURRENT_FIELDS),
        "daily": ",".join(DAILY_FIELDS),
        "timezone": "Africa/Lagos",
        "forecast_days": 2,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(settings.open_meteo_base_url, params=params)
        response.raise_for_status()
        return response.json()


async def fetch_historical_weather(start_date: date, end_date: date) -> dict[str, Any]:
    """Fetch hourly historical atmospheric data for Lagos, used for model training."""
    params = {
        "latitude": settings.lat,
        "longitude": settings.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": ",".join(ARCHIVE_HOURLY_FIELDS),
        "timezone": "Africa/Lagos",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(settings.open_meteo_archive_url, params=params)
        response.raise_for_status()
        return response.json()
