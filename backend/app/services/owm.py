"""Fetches current weather from OpenWeatherMap, mapped to our Open-Meteo field names."""

import logging
import math
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

OWM_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def _dew_point_2m(temp_c: float, humidity_pct: float) -> float:
    """Magnus formula approximation, matching what Open-Meteo derives server-side."""
    a, b = 17.62, 243.12
    gamma = (a * temp_c) / (b + temp_c) + math.log(max(humidity_pct, 1) / 100.0)
    return (b * gamma) / (a - gamma)


async def fetch_owm_current(lat: float | None = None, lon: float | None = None) -> dict[str, Any] | None:
    """Fetch current conditions from OpenWeatherMap, or None if unavailable/misconfigured."""
    if not settings.owm_api_key:
        logger.warning("owm.fetch_owm_current: no API key configured, skipping")
        return None

    latitude = lat if lat is not None else settings.lagos_lat
    longitude = lon if lon is not None else settings.lagos_lon
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.owm_api_key,
        "units": "metric",
    }

    logger.info("owm.fetch_owm_current: starting (lat=%s, lon=%s)", latitude, longitude)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OWM_BASE_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("owm.fetch_owm_current: request failed: %s", exc)
        return None

    payload = response.json()
    main = payload.get("main", {})
    wind = payload.get("wind", {})
    clouds = payload.get("clouds", {})
    rain = payload.get("rain", {})
    snow = payload.get("snow", {})

    temperature_2m = main.get("temp")
    relative_humidity_2m = main.get("humidity")

    current = {
        "temperature_2m": temperature_2m,
        "relative_humidity_2m": relative_humidity_2m,
        "dew_point_2m": _dew_point_2m(temperature_2m, relative_humidity_2m),
        "surface_pressure": main.get("pressure"),
        "cloud_cover": clouds.get("all"),
        "wind_speed_10m": wind.get("speed"),
        "wind_direction_10m": wind.get("deg"),
        "precipitation": rain.get("1h", snow.get("1h", 0.0)),
        "time": datetime.fromtimestamp(payload.get("dt", 0), tz=timezone.utc).isoformat(),
    }

    logger.info("owm.fetch_owm_current: success (lat=%s, lon=%s)", latitude, longitude)
    return {
        "latitude": latitude,
        "longitude": longitude,
        "current": current,
        "source": "owm",
    }
