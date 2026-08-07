"""Loads the trained Random Forest model and produces rain predictions."""

import json
import logging
from pathlib import Path

import joblib
import pandas as pd

from app.core.config import settings
from app.ml.features import build_feature_dict

logger = logging.getLogger("uvicorn.error")


class ModelNotTrainedError(RuntimeError):
    """Raised when a prediction is requested before a model has been trained."""


class RainPredictor:
    def __init__(self, model_path: str | None = None, feature_columns_path: str | None = None):
        self._model_path = Path(model_path or settings.model_path)
        self._feature_columns_path = Path(
            feature_columns_path or (self._model_path.parent / "feature_columns.json")
        )
        self._model = None
        self._feature_columns: list[str] | None = None

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
        logger.info("RainPredictor: model loaded successfully")

    def is_ready(self) -> bool:
        return self._model_path.exists() and self._feature_columns_path.exists()

    def reload(self) -> None:
        """Force the model and feature columns to be re-read from disk on next use."""
        logger.info("RainPredictor: reload requested, will re-read from disk on next use")
        self._model = None
        self._feature_columns = None

    def predict(self, reading: dict) -> dict:
        logger.info("RainPredictor.predict: starting")
        self._ensure_loaded()

        features = build_feature_dict(reading)
        vector = pd.DataFrame([[features[column] for column in self._feature_columns]], columns=self._feature_columns)

        probabilities = self._model.predict_proba(vector)[0]
        classes = list(self._model.classes_)
        rain_probability = float(probabilities[classes.index(1)])
        will_rain = rain_probability >= 0.5
        confidence = rain_probability if will_rain else 1 - rain_probability
        logger.info(
            "RainPredictor.predict: result=%s rain_probability=%.4f",
            "Rain" if will_rain else "No Rain",
            rain_probability,
        )

        return {
            "label": "Rain" if will_rain else "No Rain",
            "will_rain": will_rain,
            "confidence": round(confidence, 4),
            "rain_probability": round(rain_probability, 4),
            "features_used": {column: round(features[column], 4) for column in self._feature_columns},
        }


rain_predictor = RainPredictor()
