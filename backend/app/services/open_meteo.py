"""Fetches live and historical atmospheric data from Open-Meteo, defaulting to Lagos."""

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.services.owm import fetch_owm_current

logger = logging.getLogger("uvicorn.error")

LIVE_RETRY_ATTEMPTS = 5
LIVE_RETRY_DELAY_SECONDS = 15
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
    logger.info("open_meteo.fetch_live_weather: starting (lat=%s, lon=%s)", lat, lon)

    owm_data = await fetch_owm_current(lat, lon)
    if owm_data is not None:
        logger.info("open_meteo.fetch_live_weather: serving OWM reading")
        _live_cache[_cache_key(lat, lon)] = (owm_data, datetime.now(timezone.utc))
        return owm_data
    logger.warning("open_meteo.fetch_live_weather: OWM unavailable, falling back to Open-Meteo")

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
            logger.info(
                "open_meteo.fetch_live_weather: attempt %d/%d", attempt, LIVE_RETRY_ATTEMPTS
            )
            response = await client.get(settings.open_meteo_base_url, params=params)
            if response.status_code == 429 and attempt < LIVE_RETRY_ATTEMPTS:
                logger.warning(
                    "open_meteo.fetch_live_weather: 429 rate limited, waiting %ds before retry",
                    LIVE_RETRY_DELAY_SECONDS,
                )
                await asyncio.sleep(LIVE_RETRY_DELAY_SECONDS)
                continue
            if response.status_code == 429:
                logger.warning(
                    "open_meteo.fetch_live_weather: retries exhausted, looking for a fallback"
                )
                # Exhausted retries. Fall back to whatever we last cached for these
                # coordinates, however stale, before giving up entirely.
                cached = get_cached_live_weather(lat, lon)
                if cached is not None:
                    logger.info("open_meteo.fetch_live_weather: serving stale cache")
                    return cached[0]
                fallback = await _fetch_archive_fallback(lat, lon)
                if fallback is not None:
                    logger.info("open_meteo.fetch_live_weather: serving archive fallback")
                    return fallback
                logger.error("open_meteo.fetch_live_weather: no cache or fallback available")
                response.raise_for_status()
            response.raise_for_status()
            data = response.json()
            _live_cache[_cache_key(lat, lon)] = (data, datetime.now(timezone.utc))
            logger.info("open_meteo.fetch_live_weather: success, cached for (%s, %s)", lat, lon)
            return data


async def _fetch_archive_fallback(lat: float | None, lon: float | None) -> dict[str, Any] | None:
    """Last resort when the forecast API is rate limited: yesterday's noon archive reading."""
    logger.info("open_meteo._fetch_archive_fallback: starting (lat=%s, lon=%s)", lat, lon)
    yesterday = date.today() - timedelta(days=1)
    try:
        archive_data = await fetch_historical_weather(yesterday, yesterday, lat, lon)
    except httpx.HTTPError as exc:
        logger.error("open_meteo._fetch_archive_fallback: archive fetch failed: %s", exc)
        return None

    hourly = archive_data.get("hourly", {})
    times = hourly.get("time", [])
    noon_index = next((i for i, t in enumerate(times) if t.endswith("T12:00")), None)
    if noon_index is None:
        logger.error("open_meteo._fetch_archive_fallback: no noon reading found")
        return None

    current = {field: hourly[field][noon_index] for field in ARCHIVE_HOURLY_FIELDS}
    current["time"] = times[noon_index]

    return {
        "latitude": lat if lat is not None else settings.lagos_lat,
        "longitude": lon if lon is not None else settings.lagos_lon,
        "current": current,
        "source": "archive_fallback",
    }


async def fetch_historical_weather(
    start_date: date, end_date: date, lat: float | None = None, lon: float | None = None
) -> dict[str, Any]:
    """Fetch hourly historical atmospheric data for the given coordinates."""
    logger.info(
        "open_meteo.fetch_historical_weather: fetching %s -> %s (lat=%s, lon=%s)",
        start_date,
        end_date,
        lat,
        lon,
    )
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
        logger.info("open_meteo.fetch_historical_weather: success")
        return response.json()
