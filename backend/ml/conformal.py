"""Split Conformal Prediction Engine built from mathematical first principles.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Rules:
- Built from scratch (zero black-box conformal libraries).
- Uses calibration split nonconformity scores (residuals: |y - y_hat| or signed upper bound residual).
- Computes empirical quantile at (1 - alpha) * (1 + 1/n_cal).
- Implements predict_bounds() and predict_upper().
- Evaluates empirical coverage across:
  - Overall
  - By state (STA, STB, STC)
  - Rainy vs Dry periods
  - Remote vs Non-remote PHCs
- Target nominal coverage: 90% (alpha = 0.10).
- Does not fake or tune results to artificially achieve 90%. If coverage is poor, reports it truthfully.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.ml.features import DatasetSplits


@dataclass
class ConformalCoverageBreakdown:
    subgroup: str
    nominal_coverage: float
    empirical_coverage: float
    sample_count: int
    mean_interval_width: float
    status: str  # VALID (coverage >= nominal - 0.05), UNDERCOVERED, OVERCONSERVATIVE


@dataclass
class ConformalEvaluationReport:
    target: str
    nominal_confidence: float
    overall_coverage: float
    mean_interval_width: float
    calibration_size: int
    test_size: int
    quantile_q: float
    subgroup_breakdowns: List[ConformalCoverageBreakdown] = field(default_factory=list)


@dataclass
class ConformalPredictionResult:
    point_forecast: float
    lower_bound: float
    upper_bound: float
    confidence_level: float
    quantile_residual: float
    model_version: str
    calibration_version: str


class SplitConformalPredictor:
    """Split Conformal Predictor for calibrated distribution-free uncertainty intervals."""

    def __init__(
        self,
        nominal_confidence: float = 0.90,  # 90% target coverage
        calibration_version: str = "cal-v1.0",
        model_version: str = "v1.0.0",
    ) -> None:
        self.nominal_confidence = nominal_confidence
        self.alpha = 1.0 - nominal_confidence
        self.calibration_version = calibration_version
        self.model_version = model_version
        self.q_hat: Optional[float] = None
        self.residuals_cal: Optional[np.ndarray] = None

    def calibrate(
        self,
        y_cal: np.ndarray,
        y_cal_pred: np.ndarray,
    ) -> float:
        """Compute the conformal nonconformity quantile on the calibration dataset.
        Nonconformity score R_i = |y_i - y_hat_i|.
        Quantile level: ceil((n + 1) * (1 - alpha)) / n.
        """
        n_cal = len(y_cal)
        if n_cal == 0:
            raise ValueError("Calibration set must not be empty.")

        # Absolute residuals
        scores = np.sort(np.abs(y_cal - y_cal_pred))
        self.residuals_cal = scores

        # Finite-sample calibrated conformal index:
        # k = min(n_cal, int(np.ceil((n_cal + 1) * (1.0 - self.alpha))))
        # 0-indexed: k - 1
        k = min(n_cal, int(np.ceil((n_cal + 1) * (1.0 - self.alpha))))
        self.q_hat = float(scores[k - 1])

        return self.q_hat

    def predict_upper(self, point_forecast: float) -> float:
        """Return calibrated upper bound for service capacity / buffer sizing."""
        if self.q_hat is None:
            raise ValueError("Conformal predictor must be calibrated before predicting upper bounds.")
        return float(max(0.0, point_forecast + self.q_hat))

    def predict_bounds(self, point_forecast: float) -> ConformalPredictionResult:
        """Return point forecast, conformal lower bound, and calibrated upper bound."""
        if self.q_hat is None:
            raise ValueError("Conformal predictor must be calibrated before predicting bounds.")

        lower = float(max(0.0, point_forecast - self.q_hat))
        upper = float(max(0.0, point_forecast + self.q_hat))

        return ConformalPredictionResult(
            point_forecast=round(float(point_forecast), 2),
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
            confidence_level=self.nominal_confidence,
            quantile_residual=round(self.q_hat, 3),
            model_version=self.model_version,
            calibration_version=self.calibration_version,
        )

    def evaluate_coverage(
        self,
        splits: DatasetSplits,
        y_test_pred: np.ndarray,
        target_name: str = "diarrhoeal_cases",
    ) -> ConformalEvaluationReport:
        """Evaluate empirical coverage across subgroups without falsifying or tuning results.
        Subgroups:
        - Overall
        - State (STA, STB, STC)
        - Rainy vs Dry (rainfall > 5mm vs <= 5mm)
        - Remote vs Non-remote (remote_flag == 1 vs 0)
        """
        if self.q_hat is None:
            raise ValueError("Predictor is not calibrated.")

        df_test = splits.df_test.copy()
        y_true = splits.y_test.values
        y_pred = y_test_pred

        df_test["y_true"] = y_true
        df_test["y_pred"] = y_pred
        df_test["lower_bound"] = np.clip(y_pred - self.q_hat, 0, None)
        df_test["upper_bound"] = np.clip(y_pred + self.q_hat, 0, None)
        df_test["covered"] = (df_test["y_true"] >= df_test["lower_bound"]) & (df_test["y_true"] <= df_test["upper_bound"])
        df_test["interval_width"] = df_test["upper_bound"] - df_test["lower_bound"]

        breakdowns: List[ConformalCoverageBreakdown] = []

        # 1. Overall
        overall_cov = float(df_test["covered"].mean())
        mean_width = float(df_test["interval_width"].mean())
        breakdowns.append(
            self._create_breakdown("Overall Test Set", df_test)
        )

        # 2. State-wise
        for st_code in sorted(df_test["state_code"].unique()):
            sub = df_test[df_test["state_code"] == st_code]
            breakdowns.append(self._create_breakdown(f"State: {st_code}", sub))

        # 3. Rainy vs Dry
        rainy_sub = df_test[df_test["rainfall"] > 5.0]
        dry_sub = df_test[df_test["rainfall"] <= 5.0]
        breakdowns.append(self._create_breakdown("Weather: Rainy (>5mm)", rainy_sub))
        breakdowns.append(self._create_breakdown("Weather: Dry (<=5mm)", dry_sub))

        # 4. Remote vs Non-Remote
        remote_sub = df_test[df_test["remote_flag"] == 1]
        urban_sub = df_test[df_test["remote_flag"] == 0]
        breakdowns.append(self._create_breakdown("Location: Remote PHCs", remote_sub))
        breakdowns.append(self._create_breakdown("Location: Non-Remote PHCs", urban_sub))

        return ConformalEvaluationReport(
            target=target_name,
            nominal_confidence=self.nominal_confidence,
            overall_coverage=round(overall_cov, 4),
            mean_interval_width=round(mean_width, 2),
            calibration_size=len(splits.y_cal),
            test_size=len(y_true),
            quantile_q=round(self.q_hat, 3),
            subgroup_breakdowns=breakdowns,
        )

    def _create_breakdown(self, name: str, sub_df: pd.DataFrame) -> ConformalCoverageBreakdown:
        if len(sub_df) == 0:
            return ConformalCoverageBreakdown(name, self.nominal_confidence, 0.0, 0, 0.0, "NO_DATA")

        cov = float(sub_df["covered"].mean())
        width = float(sub_df["interval_width"].mean())
        count = len(sub_df)

        if cov >= (self.nominal_confidence - 0.03):
            status = "VALID_COVERAGE"
        elif cov < (self.nominal_confidence - 0.05):
            status = "UNDERCOVERED_WARNING"
        else:
            status = "BORDERLINE"

        return ConformalCoverageBreakdown(
            subgroup=name,
            nominal_coverage=self.nominal_confidence,
            empirical_coverage=round(cov, 4),
            sample_count=count,
            mean_interval_width=round(width, 2),
            status=status,
        )
