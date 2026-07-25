import asyncio
import json
from datetime import date, timedelta
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.ml.predictor import ModelNotTrainedError, rain_predictor
from app.schemas.weather import (
    HealthResponse,
    LiveReading,
    LiveWeatherResponse,
    PredictionInput,
    PredictionResponse,
)
from app.services import nasa_power, open_meteo

router = APIRouter()

MODELS_DIR = Path(settings.model_path).parent

# NASA POWER's daily near-real-time data and Open-Meteo's ERA5-based archive both need
# a few days to settle, so we look at a 7-day window ending a week ago.
NASA_COMPARE_LAG_DAYS = 7
NASA_COMPARE_WINDOW_DAYS = 7

# Same threshold used to derive the "rained" label at training time (see train_model.py).
RAIN_THRESHOLD_MM = 0.1


def _extract_current_reading(live_data: dict) -> LiveReading:
    current = live_data["current"]
    return LiveReading(
        temperature_2m=current["temperature_2m"],
        relative_humidity_2m=current["relative_humidity_2m"],
        dew_point_2m=current["dew_point_2m"],
        surface_pressure=current["surface_pressure"],
        cloud_cover=current["cloud_cover"],
        wind_speed_10m=current["wind_speed_10m"],
        wind_direction_10m=current["wind_direction_10m"],
        precipitation=current["precipitation"],
        time=current["time"],
    )


async def _fetch_noon_reading(day: date, lat: float | None = None, lon: float | None = None) -> dict | None:
    """Fetch that day's noon (12:00 local) hourly reading from the Open-Meteo archive."""
    archive_data = await open_meteo.fetch_historical_weather(day, day, lat, lon)
    hourly = archive_data.get("hourly", {})
    times = hourly.get("time", [])

    noon_index = next((i for i, t in enumerate(times) if t.endswith("T12:00")), None)
    if noon_index is None:
        return None

    return {
        "temperature_2m": hourly["temperature_2m"][noon_index],
        "relative_humidity_2m": hourly["relative_humidity_2m"][noon_index],
        "surface_pressure": hourly["surface_pressure"][noon_index],
        "cloud_cover": hourly["cloud_cover"][noon_index],
        "wind_speed_10m": hourly["wind_speed_10m"][noon_index],
        "wind_direction_10m": hourly["wind_direction_10m"][noon_index],
        "time": times[noon_index],
    }


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", model_loaded=rain_predictor.is_ready())


@router.get("/weather/live", response_model=LiveWeatherResponse)
async def get_live_weather(
    lat: float | None = Query(None, description="Latitude override; defaults to Lagos"),
    lon: float | None = Query(None, description="Longitude override; defaults to Lagos"),
):
    """Live atmospheric readings from Open-Meteo for the given coordinates (defaults to Lagos)."""
    live_data = await open_meteo.fetch_live_weather(lat, lon)
    return LiveWeatherResponse(
        location="Lagos, Nigeria" if lat is None and lon is None else "Current Location",
        latitude=live_data["latitude"],
        longitude=live_data["longitude"],
        current=_extract_current_reading(live_data),
    )


@router.post("/predict", response_model=PredictionResponse)
async def predict_rain(
    payload: PredictionInput | None = None,
    lat: float | None = Query(None, description="Latitude override; defaults to Lagos"),
    lon: float | None = Query(None, description="Longitude override; defaults to Lagos"),
):
    """Predict rain from a passed-in reading, or from a live Open-Meteo fetch if no body is sent."""
    if payload is not None:
        reading_dict = payload.model_dump()
    else:
        live_data = await open_meteo.fetch_live_weather(lat, lon)
        reading_dict = _extract_current_reading(live_data).model_dump()

    try:
        result = rain_predictor.predict(reading_dict)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return PredictionResponse(
        label=result["label"],
        will_rain=result["will_rain"],
        confidence=result["confidence"],
        rain_probability=result["rain_probability"],
        features_used=result["features_used"],
        based_on=reading_dict,
    )


@router.get("/validate")
async def validate_prediction():
    """Return the training report comparing Random Forest, Decision Tree, and Logistic Regression."""
    report_path = MODELS_DIR / "training_report.json"
    if not report_path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"No training report found at '{report_path}'. Run backend/train_model.py first.",
        )
    return json.loads(report_path.read_text())


@router.get("/nasa/compare")
async def compare_with_nasa(
    lat: float | None = Query(None, description="Latitude override; defaults to Lagos"),
    lon: float | None = Query(None, description="Longitude override; defaults to Lagos"),
):
    """
    Compare our model's predictions against NASA POWER recorded precipitation for the
    last 7 days, at the given coordinates (defaults to Lagos). For each day, we predict
    from that day's noon Open-Meteo archive reading and check it against NASA's recorded
    daily precipitation total.
    """
    end = date.today() - timedelta(days=NASA_COMPARE_LAG_DAYS)
    start = end - timedelta(days=NASA_COMPARE_WINDOW_DAYS - 1)

    try:
        power_data = await nasa_power.fetch_daily_power_data(start, end, lat, lon)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"NASA POWER request failed: {exc}") from exc

    precip_by_date = power_data.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
    candidate_days = [start + timedelta(days=offset) for offset in range(NASA_COMPARE_WINDOW_DAYS)]

    # Fetch each day's noon Open-Meteo reading concurrently instead of one-by-one, this
    # is the difference between a ~10s and a ~70s response for a 7-day window.
    noon_readings = await asyncio.gather(
        *(_fetch_noon_reading(day, lat, lon) for day in candidate_days), return_exceptions=True
    )

    days = []
    for day, noon_reading in zip(candidate_days, noon_readings):
        nasa_precip = precip_by_date.get(day.strftime("%Y%m%d"))
        if nasa_precip is None or nasa_precip < 0:
            # NASA POWER uses -999 (or omits the key) for days it has no data for yet.
            continue
        if isinstance(noon_reading, BaseException) or noon_reading is None:
            continue

        try:
            prediction = rain_predictor.predict(noon_reading)
        except ModelNotTrainedError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        actual_rain = nasa_precip >= RAIN_THRESHOLD_MM
        days.append(
            {
                "date": day.isoformat(),
                "our_prediction": prediction["label"],
                "confidence": prediction["confidence"],
                "nasa_precipitation_mm": round(nasa_precip, 2),
                "correct": prediction["will_rain"] == actual_rain,
            }
        )

    accuracy = round(sum(d["correct"] for d in days) / len(days), 4) if days else None

    return {
        "location": "Lagos, Nigeria" if lat is None and lon is None else "Current Location",
        "rain_threshold_mm": RAIN_THRESHOLD_MM,
        "days": days,
        "accuracy": accuracy,
    }
