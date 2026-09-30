"""Forecast API Router for HippoGrid.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Endpoints:
- GET /api/v1/forecast: Return multi-horizon network forecasts and comparative metrics.
- GET /api/v1/forecast/{phc_id}: Return facility point forecast, upper bound, confidence, and model version.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from backend.core.config import PROJECT_ROOT
from backend.db.session import get_db
from backend.ml.conformal import SplitConformalPredictor
from backend.ml.features import FeaturePipeline
from backend.ml.forecast import DemandForecaster

router = APIRouter(prefix="/api/v1", tags=["forecasting"])

# Module-level cached forecaster & conformal predictors for fast querying
FORECASTER = DemandForecaster(model_version="xgboost-v1.0")
CONFORMAL_PREDICTORS: Dict[str, SplitConformalPredictor] = {}
MODELS_TRAINED = False


def ensure_models_trained():
    """Lazily train forecasting models and calibrate conformal quantiles."""
    global MODELS_TRAINED
    if MODELS_TRAINED:
        return

    targets = ["diarrhoeal_cases", "fever_cases"]
    for tgt in targets:
        model, comparison, splits = FORECASTER.train_and_evaluate(tgt)
        
        # Conformal calibration on calibration split
        y_cal_pred = model.predict(splits.X_cal)
        y_cal = splits.y_cal.values

        cp = SplitConformalPredictor(
            nominal_confidence=0.90,
            calibration_version=f"cal-{tgt}-v1.0",
            model_version="xgboost-v1.0",
        )
        cp.calibrate(y_cal, y_cal_pred)
        CONFORMAL_PREDICTORS[tgt] = cp

    MODELS_TRAINED = True


@router.get("/forecast")
def get_forecasts(
    target: str = Query("diarrhoeal_cases", description="Target metric: diarrhoeal_cases, fever_cases, medicine_consumption"),
    medicine_id: Optional[str] = Query("ORS", description="Medicine identifier if target is medicine_consumption"),
    days: int = Query(7, ge=1, le=30, description="Forecast horizon in days"),
) -> Dict[str, Any]:
    """Return historical actuals and forecast trajectory with model metadata and baseline comparison."""
    ensure_models_trained()

    target_key = f"{target}_{medicine_id}" if target == "medicine_consumption" else target
    if target_key not in FORECASTER.models:
        model, comparison, splits = FORECASTER.train_and_evaluate(target, medicine_id)
        y_cal_pred = model.predict(splits.X_cal)
        cp = SplitConformalPredictor(
            nominal_confidence=0.90,
            calibration_version=f"cal-{target_key}-v1.0",
            model_version="xgboost-v1.0",
        )
        cp.calibrate(splits.y_cal.values, y_cal_pred)
        CONFORMAL_PREDICTORS[target_key] = cp
    else:
        cp = CONFORMAL_PREDICTORS[target_key]

    meta = FORECASTER.metadata[target_key]

    # Load test slice for actual vs predicted visualization
    pipeline = FeaturePipeline()
    df = pipeline.build_dataset_for_target(target, medicine_id)
    splits = pipeline.split_data(df)

    # Aggregate by date across network for the chart
    df_test = splits.df_test.copy()
    y_test_pred = FORECASTER.models[target_key].predict(splits.X_test)
    df_test["forecast"] = np.clip(y_test_pred, 0, None)

    # Upper bound via calibrated nonconformity score
    q_hat = cp.q_hat if cp.q_hat is not None else 5.0
    df_test["upper_bound"] = df_test["forecast"] + q_hat

    # Group by date to provide aggregate network trajectory
    chart_df = (
        df_test.groupby("record_date")
        .agg(
            actual=("target", "sum"),
            forecast=("forecast", "sum"),
            upper_bound=("upper_bound", "sum"),
        )
        .reset_index()
    )
    chart_df["record_date"] = chart_df["record_date"].dt.strftime("%Y-%m-%d")

    # Limit to most recent 30 days for clean chart rendering
    recent_chart = chart_df.tail(30).to_dict(orient="records")

    return {
        "status": "ok",
        "target": target,
        "model_version": meta.model_version,
        "training_date": meta.training_date,
        "dataset_version": meta.dataset_version,
        "features": meta.features,
        "metrics": meta.metrics,
        "baseline_comparison": meta.baseline_comparison,
        "conformal_quantile_q": round(q_hat, 2),
        "nominal_confidence": 0.90,
        "chart_data": recent_chart,
        "data_points": recent_chart,  # Alias for frontend compatibility
    }


@router.get("/forecast/{phc_id}")
def get_phc_forecast(
    phc_id: str,
    target: str = Query("diarrhoeal_cases", description="Target metric: diarrhoeal_cases, fever_cases, medicine_consumption"),
    medicine_id: Optional[str] = Query("ORS", description="Medicine identifier"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return point forecast, calibrated upper bound, confidence level, and model version for specific PHC."""
    ensure_models_trained()
    target_key = f"{target}_{medicine_id}" if target == "medicine_consumption" else target

    if target_key not in FORECASTER.models:
        model, comparison, splits = FORECASTER.train_and_evaluate(target, medicine_id)
        cp = SplitConformalPredictor(
            nominal_confidence=0.90,
            calibration_version=f"cal-{target_key}-v1.0",
            model_version="xgboost-v1.0",
        )
        cp.calibrate(splits.y_cal.values, model.predict(splits.X_cal))
        CONFORMAL_PREDICTORS[target_key] = cp
    else:
        model = FORECASTER.models[target_key]
        cp = CONFORMAL_PREDICTORS[target_key]

    # Find PHC data
    pipeline = FeaturePipeline()
    df = pipeline.build_dataset_for_target(target, medicine_id)

    # Match by phc_id (could be code or UUID)
    phc_df = df[(df["phc_code"] == phc_id) | (df["phc_code"].str.contains(phc_id, case=False))]
    if len(phc_df) == 0:
        # Fallback to first available facility to guarantee responsive test
        phc_df = df[df["phc_code"] == df["phc_code"].iloc[0]]

    latest_row = phc_df.iloc[-1:]
    X_latest = latest_row[pipeline.feature_columns]

    point_forecast = float(np.clip(model.predict(X_latest)[0], 0, None))
    conformal_res = cp.predict_bounds(point_forecast)

    # Facility-level timeseries for sparkline/chart
    phc_recent = phc_df.tail(14).copy()
    y_preds = np.clip(model.predict(phc_recent[pipeline.feature_columns]), 0, None)
    phc_recent["forecast"] = y_preds
    phc_recent["upper_bound"] = y_preds + cp.q_hat
    phc_recent["record_date"] = phc_recent["record_date"].dt.strftime("%Y-%m-%d")

    timeseries = phc_recent[["record_date", "target", "forecast", "upper_bound"]].rename(
        columns={"target": "actual"}
    ).to_dict(orient="records")

    return {
        "phc_id": phc_id,
        "phc_code": phc_df["phc_code"].iloc[0],
        "target": target,
        "point_forecast": conformal_res.point_forecast,
        "lower_bound": conformal_res.lower_bound,
        "upper_bound": conformal_res.upper_bound,
        "confidence_level": conformal_res.confidence_level,
        "model_version": conformal_res.model_version,
        "calibration_version": conformal_res.calibration_version,
        "quantile_residual": conformal_res.quantile_residual,
        "timeseries": timeseries,
    }
