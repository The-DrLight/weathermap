"""Fetches atmospheric data from NASA POWER, defaulting to Lagos, used to validate Open-Meteo readings."""

import logging
from datetime import date
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

POWER_PARAMETERS = [
    "T2M",
    "RH2M",
    "PS",
    "WS10M",
    "WD10M",
    "CLOUD_AMT",
    "PRECTOTCORR",
]


async def _fetch(
    url: str,
    start_date: date,
    end_date: date,
    lat: float | None = None,
    lon: float | None = None,
) -> dict[str, Any]:
    params = {
        "parameters": ",".join(POWER_PARAMETERS),
        "community": "AG",
        "longitude": lon if lon is not None else settings.lagos_lon,
        "latitude": lat if lat is not None else settings.lagos_lat,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }
    logger.info("nasa_power._fetch: fetching %s -> %s from %s", start_date, end_date, url)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        logger.info("nasa_power._fetch: success")
        return response.json()


async def fetch_power_data(
    start_date: date, end_date: date, lat: float | None = None, lon: float | None = None
) -> dict[str, Any]:
    """Fetch hourly NASA POWER data for the given coordinates over the given date range."""
    logger.info("nasa_power.fetch_power_data: starting")
    return await _fetch(settings.nasa_power_base_url, start_date, end_date, lat, lon)


async def fetch_daily_power_data(
    start_date: date, end_date: date, lat: float | None = None, lon: float | None = None
) -> dict[str, Any]:
    """Fetch daily NASA POWER data for the given coordinates over the given date range."""
    logger.info("nasa_power.fetch_daily_power_data: starting")
    return await _fetch(settings.nasa_power_daily_url, start_date, end_date, lat, lon)
