import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import train_model  # noqa: E402
from app.ml.features import HISTORY_FEATURE_COLUMNS, build_history_features  # noqa: E402
from app.ml.predictor import RainPredictor  # noqa: E402


def _synthetic_hourly(n: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="h"),
            "temperature_2m": 25 + rng.normal(0, 2, n),
            "relative_humidity_2m": rng.uniform(50, 99, n),
            "surface_pressure": 1010 + rng.normal(0, 2, n).cumsum() * 0.3,
            "wind_speed_10m": rng.uniform(0, 15, n),
            "wind_direction_10m": rng.uniform(0, 360, n),
            "cloud_cover": rng.uniform(0, 100, n),
            "precipitation": np.where(rng.random(n) < 0.3, rng.uniform(0.1, 3, n), 0.0),
        }
    )


def test_history_features_match_training_features():
    """The scalar live-time features must equal the vectorized training-time ones."""
    raw = _synthetic_hourly()
    engineered = train_model.engineer_features(raw)

    for row_idx in (0, 10, len(engineered) - 1):
        t = engineered.loc[row_idx, "time"]
        pos = int(raw.index[raw["time"] == t][0])
        history = raw.iloc[pos - 6 : pos + 1].to_dict("records")
        live = build_history_features(history)
        assert live is not None
        for col in HISTORY_FEATURE_COLUMNS:
            assert live[col] == pytest.approx(engineered.loc[row_idx, col]), col


def test_history_features_none_when_insufficient_or_missing():
    raw = _synthetic_hourly()
    history = raw.iloc[:7].to_dict("records")
    assert build_history_features(history[:6]) is None
    assert build_history_features(None) is None
    history[3]["surface_pressure"] = None
    assert build_history_features(history) is None


def test_predictor_uses_history_model_and_falls_back():
    predictor = RainPredictor()
    if not predictor.is_ready():
        pytest.skip("model not trained")
    raw = _synthetic_hourly()
    history = raw.iloc[:7].to_dict("records")
    reading = {
        "temperature_2m": 26.0,
        "relative_humidity_2m": 90.0,
        "surface_pressure": 1009.0,
        "cloud_cover": 90.0,
        "wind_speed_10m": 10.0,
        "wind_direction_10m": 220.0,
        "time": "2026-07-10T15:00:00",
    }
    with_history = predictor.predict(reading, history)
    without_history = predictor.predict(reading)
    assert set(HISTORY_FEATURE_COLUMNS) <= set(with_history["features_used"])
    assert not set(HISTORY_FEATURE_COLUMNS) & set(without_history["features_used"])
