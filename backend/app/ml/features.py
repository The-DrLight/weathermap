"""Feature engineering shared by the training script and the live predictor.

These scalar helpers mirror the vectorized (pandas) versions in
`backend/train_model.py` exactly — if the formulas ever diverge, training
and serving will disagree on what a feature means.
"""

import math
from datetime import datetime


def compute_dew_point(temp_c: float, relative_humidity: float) -> float:
    """Magnus formula dew point approximation, valid for 0-60C / 1-100% RH."""
    a, b = 17.27, 237.7
    alpha = (a * temp_c) / (b + temp_c) + math.log(relative_humidity / 100.0)
    return (b * alpha) / (a - alpha)


def compute_wind_components(wind_speed: float, wind_direction_deg: float) -> tuple[float, float]:
    """Decompose wind speed/direction into east-west (u) and north-south (v) vectors."""
    direction_rad = math.radians(wind_direction_deg)
    u = -wind_speed * math.sin(direction_rad)
    v = -wind_speed * math.cos(direction_rad)
    return u, v


def compute_cyclical_time(dt: datetime) -> dict[str, float]:
    return {
        "hour_sin": math.sin(2 * math.pi * dt.hour / 24),
        "hour_cos": math.cos(2 * math.pi * dt.hour / 24),
        "month_sin": math.sin(2 * math.pi * dt.month / 12),
        "month_cos": math.cos(2 * math.pi * dt.month / 12),
    }


def build_feature_dict(reading: dict) -> dict[str, float]:
    """
    Derive the full engineered feature set from a raw weather reading.

    Expects `reading` to contain: temperature_2m, relative_humidity_2m,
    surface_pressure, cloud_cover, wind_speed_10m, wind_direction_10m, and
    time (an ISO8601 timestamp string). Any other keys are ignored.
    """
    temperature = float(reading["temperature_2m"])
    humidity = float(reading["relative_humidity_2m"])
    wind_speed = float(reading["wind_speed_10m"])
    wind_direction = float(reading["wind_direction_10m"])
    dt = datetime.fromisoformat(reading["time"])

    wind_u, wind_v = compute_wind_components(wind_speed, wind_direction)

    return {
        "temperature_2m": temperature,
        "relative_humidity_2m": humidity,
        "dew_point_2m": compute_dew_point(temperature, humidity),
        "surface_pressure": float(reading["surface_pressure"]),
        "cloud_cover": float(reading["cloud_cover"]),
        "wind_u": wind_u,
        "wind_v": wind_v,
        **compute_cyclical_time(dt),
    }
