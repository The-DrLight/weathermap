from pydantic import BaseModel, ConfigDict


class LiveReading(BaseModel):
    temperature_2m: float
    relative_humidity_2m: float
    dew_point_2m: float
    surface_pressure: float
    cloud_cover: float
    wind_speed_10m: float
    wind_direction_10m: float
    precipitation: float
    time: str


class LiveWeatherResponse(BaseModel):
    location: str = "Lagos, Nigeria"
    latitude: float
    longitude: float
    current: LiveReading


class PredictionInput(BaseModel):
    """Optional payload for POST /predict. Omit the body to use a live Open-Meteo reading."""

    temperature_2m: float
    relative_humidity_2m: float
    surface_pressure: float
    cloud_cover: float
    wind_speed_10m: float
    wind_direction_10m: float
    time: str


class PredictionResponse(BaseModel):
    label: str
    will_rain: bool
    confidence: float
    rain_probability: float
    features_used: dict[str, float]
    based_on: dict


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
