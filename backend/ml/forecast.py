"""HippoGrid Demand & Caseload Forecasting Engine using XGBoost.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Targets:
- diarrhoeal_cases
- fever_cases
- medicine_consumption (e.g. ORS, zinc, paracetamol)

Baselines for comparison:
1. Same weekday previous week (lag 7)
2. 7-day moving average (rolling mean 7)

Metrics:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- sMAPE (Symmetric Mean Absolute Percentage Error)

Stores model metadata, training configuration, evaluation metrics, and persists forecast records to Supabase.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
from sqlalchemy.orm import Session
from backend.core.config import PROJECT_ROOT
from backend.ml.features import DatasetSplits, FeaturePipeline

MODEL_REGISTRY_DIR = PROJECT_ROOT / "models"
MODEL_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)


def calculate_smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Symmetric Mean Absolute Percentage Error (sMAPE in %)."""
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    # Avoid zero division
    zero_mask = denominator == 0
    diff = np.abs(y_pred - y_true)
    ratios = np.zeros_like(diff, dtype=float)
    ratios[~zero_mask] = (diff[~zero_mask] / denominator[~zero_mask]) * 100.0
    return float(np.mean(ratios))


@dataclass
class ModelMetrics:
    mae: float
    rmse: float
    smape: float


@dataclass
class BaselineComparison:
    xgboost: ModelMetrics
    same_weekday_prev_week: ModelMetrics
    moving_average_7day: ModelMetrics


@dataclass
class ForecastModelMetadata:
    model_version: str
    target: str
    training_date: str
    features: List[str]
    dataset_version: str
    metrics: Dict[str, Any]
    baseline_comparison: Dict[str, Any]


class DemandForecaster:
    """Trains, evaluates, and predicts health center demand using XGBoost."""

    def __init__(
        self,
        model_version: str = "v1.0.0",
        random_seed: int = 42,
    ) -> None:
        self.model_version = model_version
        self.random_seed = random_seed
        self.pipeline = FeaturePipeline()
        self.models: Dict[str, xgb.XGBRegressor] = {}
        self.metadata: Dict[str, ForecastModelMetadata] = {}

    def train_and_evaluate(
        self,
        target_name: str,
        medicine_id: Optional[str] = "ORS",
    ) -> Tuple[xgb.XGBRegressor, BaselineComparison, DatasetSplits]:
        """Train XGBoost model, evaluate against baselines on test set, and store metadata."""
        df = self.pipeline.build_dataset_for_target(target_name, medicine_id)
        splits = self.pipeline.split_data(df)

        # Configure XGBoost regressor with deterministic seed 42
        model = xgb.XGBRegressor(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=self.random_seed,
            n_jobs=2,
        )

        # Train exclusively on training set (no data leakage)
        model.fit(
            splits.X_train,
            splits.y_train,
            eval_set=[(splits.X_cal, splits.y_cal)],
            verbose=False,
        )

        # Evaluate on Test Set
        y_test = splits.y_test.values
        y_pred = model.predict(splits.X_test)
        y_pred = np.clip(y_pred, 0, None)  # demand cannot be negative

        # Baselines
        base_prev_week = splits.df_test["baseline_same_weekday_prev_week"].values
        base_ma7 = splits.df_test["baseline_7day_moving_avg"].values

        # Compute Metrics
        xgb_metrics = ModelMetrics(
            mae=round(float(mean_absolute_error(y_test, y_pred)), 3),
            rmse=round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 3),
            smape=round(calculate_smape(y_test, y_pred), 2),
        )

        prev_week_metrics = ModelMetrics(
            mae=round(float(mean_absolute_error(y_test, base_prev_week)), 3),
            rmse=round(float(np.sqrt(mean_squared_error(y_test, base_prev_week))), 3),
            smape=round(calculate_smape(y_test, base_prev_week), 2),
        )

        ma7_metrics = ModelMetrics(
            mae=round(float(mean_absolute_error(y_test, base_ma7)), 3),
            rmse=round(float(np.sqrt(mean_squared_error(y_test, base_ma7))), 3),
            smape=round(calculate_smape(y_test, base_ma7), 2),
        )

        comparison = BaselineComparison(
            xgboost=xgb_metrics,
            same_weekday_prev_week=prev_week_metrics,
            moving_average_7day=ma7_metrics,
        )

        # Store model & metadata
        target_key = f"{target_name}_{medicine_id}" if target_name == "medicine_consumption" else target_name
        self.models[target_key] = model
        self.metadata[target_key] = ForecastModelMetadata(
            model_version=self.model_version,
            target=target_key,
            training_date=datetime.utcnow().isoformat(),
            features=splits.feature_names,
            dataset_version="hippogrid-phase2-v1",
            metrics=asdict(xgb_metrics),
            baseline_comparison=asdict(comparison),
        )

        return model, comparison, splits

    def persist_forecasts_to_db(
        self,
        db: Session,
        phc_id_map: Dict[str, str],
        service_id_map: Dict[str, str],
        target_name: str,
        df_predictions: pd.DataFrame,
    ) -> int:
        """Persist generated forecasts to Supabase PostgreSQL table 'forecasts'."""
        from sqlalchemy import text
        records_inserted = 0

        for _, row in df_predictions.iterrows():
            phc_code = row["phc_code"]
            db_phc_id = phc_id_map.get(phc_code)
            if not db_phc_id:
                continue

            target_metric = target_name
            service_id = service_id_map.get(target_name, "diarrhoeal_care")
            horizon_hours = int(row.get("horizon_hours", 24))
            pred_val = float(row["prediction"])

            db.execute(
                text("""
                    INSERT INTO forecasts (
                        phc_id, service_id, target_metric, forecast_horizon_hours,
                        predicted_value, model_version, generated_at
                    ) VALUES (
                        :phc_id, :service_id, :target_metric, :horizon_hours,
                        :predicted_value, :model_version, NOW()
                    )
                """),
                {
                    "phc_id": db_phc_id,
                    "service_id": service_id,
                    "target_metric": target_metric,
                    "horizon_hours": horizon_hours,
                    "predicted_value": round(pred_val, 2),
                    "model_version": self.model_version,
                },
            )
            records_inserted += 1

        db.commit()
        return records_inserted
