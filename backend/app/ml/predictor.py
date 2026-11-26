"""Loads the trained rain models and produces rain predictions.

Two models are trained: the main one uses recent-hour trend features and needs
a short weather history; the base one uses only the current snapshot and is
the fallback when no history is available.
"""

import json
import logging
from pathlib import Path

import joblib
import pandas as pd

from app.core.config import settings
from app.ml.features import HISTORY_FEATURE_COLUMNS, build_feature_dict, build_history_features

logger = logging.getLogger("uvicorn.error")


class ModelNotTrainedError(RuntimeError):
    """Raised when a prediction is requested before a model has been trained."""


class RainPredictor:
    def __init__(self, model_path: str | None = None, feature_columns_path: str | None = None):
        self._model_path = Path(model_path or settings.model_path)
        self._feature_columns_path = Path(
            feature_columns_path or (self._model_path.parent / "feature_columns.json")
        )
        self._base_model_path = self._model_path.parent / "rain_model_base.joblib"
        self._base_feature_columns_path = self._model_path.parent / "feature_columns_base.json"
        self._model = None
        self._feature_columns: list[str] | None = None
        self._base_model = None
        self._base_feature_columns: list[str] | None = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        logger.info("RainPredictor: loading model from '%s'", self._model_path)
        if not self._model_path.exists():
            logger.error("RainPredictor: model file missing at '%s'", self._model_path)
            raise ModelNotTrainedError(
                f"No trained model found at '{self._model_path}'. Run backend/train_model.py first."
            )
        if not self._feature_columns_path.exists():
            logger.error(
                "RainPredictor: feature columns file missing at '%s'", self._feature_columns_path
            )
            raise ModelNotTrainedError(
                f"No feature columns file found at '{self._feature_columns_path}'. "
                "Run backend/train_model.py first."
            )
        self._model = joblib.load(self._model_path)
        self._feature_columns = json.loads(self._feature_columns_path.read_text())
        if self._base_model_path.exists() and self._base_feature_columns_path.exists():
            self._base_model = joblib.load(self._base_model_path)
            self._base_feature_columns = json.loads(self._base_feature_columns_path.read_text())
        logger.info("RainPredictor: model loaded successfully")

    def is_ready(self) -> bool:
        return self._model_path.exists() and self._feature_columns_path.exists()

    def reload(self) -> None:
        """Force the models and feature columns to be re-read from disk on next use."""
        logger.info("RainPredictor: reload requested, will re-read from disk on next use")
        self._model = None
        self._feature_columns = None
        self._base_model = None
        self._base_feature_columns = None

    def predict(self, reading: dict, history: list[dict] | None = None) -> dict:
        """
        Predict rain for `reading`. Pass `history` (hourly observations, oldest first,
        last item = current hour) to use the more accurate trend-aware model; without
        usable history the snapshot-only model is used.
        """
        logger.info("RainPredictor.predict: starting")
        self._ensure_loaded()

        has_history = build_history_features(history) is not None
        if has_history or self._base_model is None:
            model, columns = self._model, self._feature_columns
        else:
            model, columns = self._base_model, self._base_feature_columns
        if not has_history and set(HISTORY_FEATURE_COLUMNS) & set(columns):
            raise ModelNotTrainedError(
                "Recent weather history is required by the trained model, but none was available. "
                "Re-run backend/train_model.py to also build the fallback model."
            )

        features = build_feature_dict(reading, history)
        vector = pd.DataFrame([[features[column] for column in columns]], columns=columns)

        probabilities = model.predict_proba(vector)[0]
        classes = list(model.classes_)
        rain_probability = float(probabilities[classes.index(1)])
        will_rain = rain_probability >= 0.5
        confidence = rain_probability if will_rain else 1 - rain_probability
        logger.info(
            "RainPredictor.predict: result=%s rain_probability=%.4f history=%s",
            "Rain" if will_rain else "No Rain",
            rain_probability,
            has_history,
        )

        return {
            "label": "Rain" if will_rain else "No Rain",
            "will_rain": will_rain,
            "confidence": round(confidence, 4),
            "rain_probability": round(rain_probability, 4),
            "features_used": {column: round(features[column], 4) for column in columns},
        }


rain_predictor = RainPredictor()
