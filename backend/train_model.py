"""
Trains the rain-prediction model on 4 years of hourly Lagos historical
weather data from the Open-Meteo archive API.

Pipeline:
  1. Fetch hourly historical data (temperature, humidity, pressure, wind,
     cloud cover, precipitation) for Lagos (6.5244N, 3.3792E).
  2. Engineer features: dew point (Magnus formula), wind U/V components,
     cyclical hour/month encoding, and the rain label.
  3. Split chronologically (oldest 64% train, next 16% validation, newest 20%
     test) so the test set is genuinely "future" data. Train Random Forest,
     Gradient Boosting, Decision Tree, and Logistic Regression and compare them
     on accuracy, precision, recall, F1, ROC AUC, and confusion matrix.
  4. Pick the model with the best validation F1, refit it on all data, and
     persist it with its feature column order and a training report.

Run with: python train_model.py            (fetch fresh data from Open-Meteo)
          python train_model.py --use-cache (reuse data/lagos_historical_raw.csv)
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    precision_score,
    recall_score,
)
from sklearn.tree import DecisionTreeClassifier

LAT = 6.5244
LON = 3.3792
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "cloud_cover",
    "precipitation",
]

YEARS_OF_HISTORY = 4
ARCHIVE_LAG_DAYS = 7  # ERA5-based archive data isn't available for the most recent days
CHUNK_DAYS = 364  # keep individual requests bounded
CHUNK_DELAY_SECONDS = 8  # pause between chunk fetches to avoid Open-Meteo rate limiting
STARTUP_DELAY_SECONDS = 30  # let the server and any initial frontend calls settle first
CHUNK_MAX_RETRIES = 3
CHUNK_RETRY_WAIT_SECONDS = 30
RAIN_THRESHOLD_MM = 0.1
TEST_FRACTION = 0.2
VAL_FRACTION = 0.16
RANDOM_STATE = 42

BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / "data"
MODELS_DIR = BACKEND_DIR / "models"

# Snapshot-only features: used by the fallback model when no recent history is available.
BASE_FEATURE_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "surface_pressure",
    "cloud_cover",
    "wind_u",
    "wind_v",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
]
# Trend and persistence features from the previous 6 hours (mirrors
# app/ml/features.py:build_history_features).
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
FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + HISTORY_FEATURE_COLUMNS
TARGET_COLUMN = "rained"


def fetch_chunk(client: httpx.Client, start: date, end: date) -> pd.DataFrame:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": ",".join(HOURLY_FIELDS),
        "timezone": "Africa/Lagos",
    }
    for attempt in range(1, CHUNK_MAX_RETRIES + 1):
        response = client.get(ARCHIVE_URL, params=params)
        if response.status_code == 429 and attempt < CHUNK_MAX_RETRIES:
            print(
                f"  429 rate limited fetching {start} -> {end}, "
                f"waiting {CHUNK_RETRY_WAIT_SECONDS}s (attempt {attempt}/{CHUNK_MAX_RETRIES})"
            )
            time.sleep(CHUNK_RETRY_WAIT_SECONDS)
            continue
        response.raise_for_status()
        return pd.DataFrame(response.json()["hourly"])
    raise RuntimeError(f"Failed to fetch chunk {start} -> {end} after {CHUNK_MAX_RETRIES} attempts")


def fetch_historical_data() -> pd.DataFrame:
    end = date.today() - timedelta(days=ARCHIVE_LAG_DAYS)
    start_overall = end - timedelta(days=365 * YEARS_OF_HISTORY)

    print(f"  waiting {STARTUP_DELAY_SECONDS}s before first fetch...")
    time.sleep(STARTUP_DELAY_SECONDS)

    frames = []
    with httpx.Client(timeout=60.0) as client:
        chunk_start = start_overall
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), end)
            print(f"  fetching {chunk_start} -> {chunk_end}")
            frames.append(fetch_chunk(client, chunk_start, chunk_end))
            chunk_start = chunk_end + timedelta(days=1)
            if chunk_start < end:
                time.sleep(CHUNK_DELAY_SECONDS)

    df = pd.concat(frames, ignore_index=True)
    df["time"] = pd.to_datetime(df["time"])
    return df.dropna().reset_index(drop=True)


def compute_dew_point(temp_c: pd.Series, relative_humidity: pd.Series) -> pd.Series:
    """Magnus formula dew point approximation, valid for 0-60C / 1-100% RH."""
    a, b = 17.27, 237.7
    alpha = (a * temp_c) / (b + temp_c) + np.log(relative_humidity / 100.0)
    return (b * alpha) / (a - alpha)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["dew_point_2m"] = compute_dew_point(df["temperature_2m"], df["relative_humidity_2m"])

    direction_rad = np.deg2rad(df["wind_direction_10m"])
    df["wind_u"] = -df["wind_speed_10m"] * np.sin(direction_rad)
    df["wind_v"] = -df["wind_speed_10m"] * np.cos(direction_rad)

    hour = df["time"].dt.hour
    month = df["time"].dt.month
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["month_sin"] = np.sin(2 * np.pi * month / 12)
    df["month_cos"] = np.cos(2 * np.pi * month / 12)

    df[TARGET_COLUMN] = (df["precipitation"] >= RAIN_THRESHOLD_MM).astype(int)

    # Trend/persistence features. The data is strictly hourly, so shift(n) is n hours back.
    df["dP_1h"] = df["surface_pressure"] - df["surface_pressure"].shift(1)
    df["dP_3h"] = df["surface_pressure"] - df["surface_pressure"].shift(3)
    df["dP_6h"] = df["surface_pressure"] - df["surface_pressure"].shift(6)
    df["dRH_3h"] = df["relative_humidity_2m"] - df["relative_humidity_2m"].shift(3)
    df["dT_3h"] = df["temperature_2m"] - df["temperature_2m"].shift(3)
    df["dCloud_3h"] = df["cloud_cover"] - df["cloud_cover"].shift(3)
    df["dDew_3h"] = df["dew_point_2m"] - df["dew_point_2m"].shift(3)
    df["rain_prev_1h"] = df[TARGET_COLUMN].shift(1)
    df["rain_prev_3h_sum"] = sum(df[TARGET_COLUMN].shift(k) for k in (1, 2, 3))

    return df.dropna().reset_index(drop=True)


def evaluate(name: str, model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    return {
        "model": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(auc), 4),
        "confusion_matrix": {
            "true_negative": int(cm[0, 0]),
            "false_positive": int(cm[0, 1]),
            "false_negative": int(cm[1, 0]),
            "true_positive": int(cm[1, 1]),
        },
    }


def print_comparison_table(results: list[dict]) -> None:
    header = f"{'Model':<22}{'Accuracy':>10}{'Precision':>11}{'Recall':>9}{'F1':>8}{'AUC':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['model']:<22}{r['accuracy']:>10.4f}{r['precision']:>11.4f}"
            f"{r['recall']:>9.4f}{r['f1_score']:>8.4f}{r['roc_auc']:>8.4f}"
        )


def print_confusion_matrices(results: list[dict]) -> None:
    for r in results:
        cm = r["confusion_matrix"]
        print(f"\n{r['model']} confusion matrix:")
        print(f"{'':16}{'Pred: No Rain':>16}{'Pred: Rain':>14}")
        print(f"{'Actual: No Rain':16}{cm['true_negative']:>16}{cm['false_positive']:>14}")
        print(f"{'Actual: Rain':16}{cm['false_negative']:>16}{cm['true_positive']:>14}")


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)

    raw_path = DATA_DIR / "lagos_historical_raw.csv"
    if "--use-cache" in sys.argv and raw_path.exists():
        print(f"Using cached historical data from {raw_path}")
        raw = pd.read_csv(raw_path, parse_dates=["time"])
    else:
        print(f"Fetching {YEARS_OF_HISTORY} years of hourly Lagos historical data from Open-Meteo...")
        raw = fetch_historical_data()
        raw.to_csv(raw_path, index=False)
    print(f"Loaded {len(raw)} hourly rows.")
    raw = raw.sort_values("time").reset_index(drop=True)

    print("Engineering features (dew point, wind U/V, cyclical time encoding, rain label)...")
    df = engineer_features(raw)
    df.to_csv(DATA_DIR / "lagos_historical_features.csv", index=False)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    print(f"Rows after cleaning: {len(df)}  |  Rain rate: {y.mean():.2%}")

    # Chronological split: no future rows leak into training.
    n = len(df)
    test_start = int(n * (1 - TEST_FRACTION))
    val_start = int(n * (1 - TEST_FRACTION - VAL_FRACTION))
    X_train, y_train = X.iloc[:val_start], y.iloc[:val_start]
    X_val, y_val = X.iloc[val_start:test_start], y.iloc[val_start:test_start]
    X_test, y_test = X.iloc[test_start:], y.iloc[test_start:]
    print(f"Train rows: {len(X_train)}  |  Val rows: {len(X_val)}  |  Test rows: {len(X_test)}")

    def make_models() -> dict:
        return {
            "Random Forest": RandomForestClassifier(
                n_estimators=300,
                min_samples_leaf=5,
                random_state=RANDOM_STATE,
                n_jobs=-1,
                class_weight="balanced_subsample",
            ),
            "Gradient Boosting": HistGradientBoostingClassifier(
                max_iter=300,
                learning_rate=0.05,
                max_leaf_nodes=15,
                min_samples_leaf=40,
                l2_regularization=1.0,
                random_state=RANDOM_STATE,
                class_weight="balanced",
            ),
            "Decision Tree": DecisionTreeClassifier(
                random_state=RANDOM_STATE, class_weight="balanced"
            ),
            "Logistic Regression": LogisticRegression(
                max_iter=5000, class_weight="balanced"
            ),
        }

    results = []
    val_f1 = {}
    for name, model in make_models().items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        val_f1[name] = f1_score(y_val, model.predict(X_val), zero_division=0)
        results.append(evaluate(name, model, X_test, y_test))

    print("\nModel comparison (on chronological held-out test set, newest 20%):\n")
    print_comparison_table(results)
    print_confusion_matrices(results)

    best_model_name = max(val_f1, key=val_f1.get)
    print(f"\nBest on validation F1: {best_model_name} ({val_f1[best_model_name]:.4f})")
    best_model = make_models()[best_model_name]
    best_model.fit(X, y)  # refit on all data for deployment

    model_path = MODELS_DIR / "rain_model.joblib"
    dump(best_model, model_path)
    print(f"\nSaved {best_model_name} model to {model_path}")

    feature_columns_path = MODELS_DIR / "feature_columns.json"
    feature_columns_path.write_text(json.dumps(FEATURE_COLUMNS, indent=2))
    print(f"Saved feature column order to {feature_columns_path}")

    # Fallback model for when no recent weather history is available at prediction
    # time: same algorithm, snapshot-only features.
    base_eval_model = make_models()[best_model_name]
    base_eval_model.fit(X_train[BASE_FEATURE_COLUMNS], y_train)
    base_result = evaluate(
        f"{best_model_name} (snapshot-only fallback)", base_eval_model, X_test[BASE_FEATURE_COLUMNS], y_test
    )
    print("\nFallback (no-history) model on the same test set:\n")
    print_comparison_table([base_result])
    base_model = make_models()[best_model_name]
    base_model.fit(X[BASE_FEATURE_COLUMNS], y)
    dump(base_model, MODELS_DIR / "rain_model_base.joblib")
    (MODELS_DIR / "feature_columns_base.json").write_text(json.dumps(BASE_FEATURE_COLUMNS, indent=2))
    print("Saved fallback model and its feature columns")

    report = {
        "trained_at": pd.Timestamp.utcnow().isoformat(),
        "years_of_history": YEARS_OF_HISTORY,
        "rows_fetched": len(raw),
        "rows_used": len(df),
        "rain_rate": round(float(y.mean()), 4),
        "rain_threshold_mm": RAIN_THRESHOLD_MM,
        "split": "chronological (64% train / 16% validation / 20% test); metrics are on the test set from a train-only fit, deployed model is refit on all data",
        "train_rows": len(X_train),
        "val_rows": len(X_val),
        "test_rows": len(X_test),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "best_model": best_model_name,
        "results": results,
        "fallback_feature_columns": BASE_FEATURE_COLUMNS,
        "fallback_result": base_result,
    }
    report_path = MODELS_DIR / "training_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"Saved training report to {report_path}")


if __name__ == "__main__":
    main()
