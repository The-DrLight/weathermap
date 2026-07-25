"""Fetches live and historical atmospheric data from Open-Meteo, defaulting to Lagos."""

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
        response = await client.get(settings.open_meteo_base_url, params=params)
        response.raise_for_status()
        return response.json()


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
