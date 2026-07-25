import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.ml.predictor import ModelNotTrainedError, rain_predictor
from app.schemas.weather import (
    HealthResponse,
    LiveReading,
    LiveWeatherResponse,
    PredictionInput,
    PredictionResponse,
)
from app.services import open_meteo

router = APIRouter()

MODELS_DIR = Path(settings.model_path).parent


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


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", model_loaded=rain_predictor.is_ready())


@router.get("/weather/live", response_model=LiveWeatherResponse)
async def get_live_weather():
    """Live Lagos atmospheric readings from Open-Meteo."""
    live_data = await open_meteo.fetch_live_weather()
    return LiveWeatherResponse(
        latitude=live_data["latitude"],
        longitude=live_data["longitude"],
        current=_extract_current_reading(live_data),
    )


@router.post("/predict", response_model=PredictionResponse)
async def predict_rain(payload: PredictionInput | None = None):
    """Predict rain from a passed-in reading, or from a live Open-Meteo fetch if no body is sent."""
    if payload is not None:
        reading_dict = payload.model_dump()
    else:
        live_data = await open_meteo.fetch_live_weather()
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
