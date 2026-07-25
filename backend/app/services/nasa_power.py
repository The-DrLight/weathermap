"""Fetches Lagos atmospheric data from NASA POWER, used to validate Open-Meteo readings."""

from datetime import date
from typing import Any

import httpx

from app.core.config import settings

POWER_PARAMETERS = [
    "T2M",
    "RH2M",
    "PS",
    "WS10M",
    "WD10M",
    "CLOUD_AMT",
    "PRECTOTCORR",
]


async def fetch_power_data(start_date: date, end_date: date) -> dict[str, Any]:
    """Fetch hourly NASA POWER data for Lagos over the given date range."""
    params = {
        "parameters": ",".join(POWER_PARAMETERS),
        "community": "AG",
        "longitude": settings.lon,
        "latitude": settings.lat,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(settings.nasa_power_base_url, params=params)
        response.raise_for_status()
        return response.json()
