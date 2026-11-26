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


RAIN_THRESHOLD_MM = 0.1
HISTORY_HOURS_REQUIRED = 7  # the current hour plus the 6 hours before it

HISTORY_FEATURE_COLUMNS = [
    "dP_1h",
    "dP_3h",
    "dP_6h",
    "dRH_3h",
    "dT_3h",
    "dCloud_3h",
    "dDew_3h",
    "rain_prev_1h",
    "rain_prev_3h_sum",
]


def build_history_features(history: list[dict] | None) -> dict[str, float] | None:
    """
    Trend and persistence features from recent hourly observations.

    `history` is chronological (oldest first); its last item is the current
    hour. Each item needs temperature_2m, relative_humidity_2m,
    surface_pressure, cloud_cover and precipitation. Returns None when there
    are too few hours or any value is missing, so callers can fall back to the
    snapshot-only model.
    """
    if not history or len(history) < HISTORY_HOURS_REQUIRED:
        return None
    hours = history[-HISTORY_HOURS_REQUIRED:]
    try:
        pressure = [float(h["surface_pressure"]) for h in hours]
        humidity = [float(h["relative_humidity_2m"]) for h in hours]
        temperature = [float(h["temperature_2m"]) for h in hours]
        cloud = [float(h["cloud_cover"]) for h in hours]
        precipitation = [float(h["precipitation"]) for h in hours]
    except (KeyError, TypeError, ValueError):
        return None

    dew = [compute_dew_point(t, rh) for t, rh in zip(temperature, humidity)]
    rained = [1.0 if p >= RAIN_THRESHOLD_MM else 0.0 for p in precipitation]

    return {
        "dP_1h": pressure[-1] - pressure[-2],
        "dP_3h": pressure[-1] - pressure[-4],
        "dP_6h": pressure[-1] - pressure[-7],
        "dRH_3h": humidity[-1] - humidity[-4],
        "dT_3h": temperature[-1] - temperature[-4],
        "dCloud_3h": cloud[-1] - cloud[-4],
        "dDew_3h": dew[-1] - dew[-4],
        "rain_prev_1h": rained[-2],
        "rain_prev_3h_sum": sum(rained[-4:-1]),
    }


def build_feature_dict(reading: dict, history: list[dict] | None = None) -> dict[str, float]:
    """
    Derive the full engineered feature set from a raw weather reading.

    Expects `reading` to contain: temperature_2m, relative_humidity_2m,
    surface_pressure, cloud_cover, wind_speed_10m, wind_direction_10m, and
    time (an ISO8601 timestamp string). Any other keys are ignored. If
    `history` (see build_history_features) is usable, the trend and
    persistence features are included too.
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
        **(build_history_features(history) or {}),
    }
