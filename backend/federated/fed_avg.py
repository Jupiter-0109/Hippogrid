"""HippoGrid Federated Learning Module.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Purpose:
Allow low-history states (State C with only 2 major flood events)
to benefit from disruption-response patterns learned by high-history states
(State A with 18 months, State B with 12 months) without sharing raw patient rows.

Clients:
- Client A: State A (6,564 telemetry records)
- Client B: State B (4,380 telemetry records)
- Client C: State C normal baseline (6,420 telemetry records)

Model:
Rainfall features -> Demand uplift (diarrhoeal cases)
Features: rainfall, rainfall_lag_1, rainfall_lag_2, rainfall_lag_3, rainfall_lag_4

Algorithm:
FedAvg (Federated Averaging), 10 communication rounds.
Client weighting: n_k / N

CRITICAL DIRECTIVES:
- Do not claim formal differential privacy guarantees.
- Python 3.10.7 strict compatibility.
- Transparent FedAvg implementation avoiding external gRPC server fragility.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.core.config import PROJECT_ROOT

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


@dataclass
class FederatedModelWeights:
    """Explicit model weights for transparent parameter tracking."""
    coef: np.ndarray  # Shape: (input_dim,)
    intercept: float

    @property
    def parameter_count(self) -> int:
        return self.coef.size + 1

    def copy(self) -> "FederatedModelWeights":
        return FederatedModelWeights(
            coef=self.coef.copy(),
            intercept=float(self.intercept),
        )


class LinearUpliftRegressor:
    """Gradient-descent linear regressor for client local training and FedAvg parameter updates."""

    def __init__(self, input_dim: int = 5, seed: int = 42) -> None:
        self.input_dim = input_dim
        self.seed = seed
        rng = np.random.RandomState(seed)
        self.weights = FederatedModelWeights(
            coef=rng.randn(input_dim) * 0.01,
            intercept=0.0,
        )

    def predict(self, X: np.ndarray, weights: Optional[FederatedModelWeights] = None) -> np.ndarray:
        w = weights or self.weights
        return np.dot(X, w.coef) + w.intercept

    def train_epoch(
        self,
        X: np.ndarray,
        y: np.ndarray,
        lr: float = 0.01,
        l2_reg: float = 1e-4,
        weights: Optional[FederatedModelWeights] = None,
    ) -> FederatedModelWeights:
        """Run one pass of gradient descent on weights."""
        w = (weights or self.weights).copy()
        n = len(X)
        if n == 0:
            return w

        y_pred = np.dot(X, w.coef) + w.intercept
        error = y_pred - y  # (N,)

        d_coef = (np.dot(X.T, error) / n) + l2_reg * w.coef
        d_intercept = np.mean(error)

        w.coef -= lr * d_coef
        w.intercept -= lr * d_intercept
        return w


class HippoGridFederatedEngine:
    """Federated Averaging engine for multi-state shock response learning."""

    def __init__(self, data_dir: Optional[Path] = None, seed: int = 42) -> None:
        self.data_dir = data_dir or RAW_DATA_DIR
        self.seed = seed
        self.feature_names = [
            "rainfall",
            "rainfall_lag_1",
            "rainfall_lag_2",
            "rainfall_lag_3",
            "rainfall_lag_4",
        ]
        self.input_dim = len(self.feature_names)

    def load_prepared_datasets(self) -> Dict[str, Any]:
        """Extract rainfall features and diarrhoeal demand across State A, B, and C."""
        phcs_path = self.data_dir / "phcs.parquet" if (self.data_dir / "phcs.parquet").exists() else self.data_dir / "phcs.csv"
        weather_path = self.data_dir / "weather.parquet" if (self.data_dir / "weather.parquet").exists() else self.data_dir / "weather.csv"
        patient_path = self.data_dir / "patient.parquet" if (self.data_dir / "patient.parquet").exists() else self.data_dir / "patient.csv"

        df_phcs = pd.read_parquet(phcs_path) if str(phcs_path).endswith(".parquet") else pd.read_csv(phcs_path)
        df_weather = pd.read_parquet(weather_path) if str(weather_path).endswith(".parquet") else pd.read_csv(weather_path)
        df_patient = pd.read_parquet(patient_path) if str(patient_path).endswith(".parquet") else pd.read_csv(patient_path)

        df_weather["record_date"] = pd.to_datetime(df_weather["record_date"])
        df_patient["record_date"] = pd.to_datetime(df_patient["record_date"])

        # Compute rainfall lags per district
        df_weather = df_weather.sort_values(["district_code", "record_date"]).reset_index(drop=True)
        df_weather["rainfall"] = df_weather["rainfall_mm"].fillna(0.0)
        for lag in [1, 2, 3, 4]:
            df_weather[f"rainfall_lag_{lag}"] = df_weather.groupby("district_code")["rainfall"].shift(lag).fillna(0.0)

        # Merge patient telemetry with PHC metadata
        merged = df_patient.merge(
            df_phcs[["code", "district_code", "state_code", "catchment_population"]],
            left_on="phc_code",
            right_on="code",
            how="inner",
        )
        weather_cols = ["district_code", "record_date", "rainfall", "rainfall_lag_1", "rainfall_lag_2", "rainfall_lag_3", "rainfall_lag_4", "is_major_flood_event"]
        merged = merged.merge(df_weather[weather_cols], on=["district_code", "record_date"], how="left")

        for col in self.feature_names:
            merged[col] = merged[col].fillna(0.0)

        # State C held-out high-rain / flood test cohort (the 2 major flood dates + 5-day post-flood window)
        stc = merged[merged["state_code"] == "STC"].copy()
        flood_dates = stc[stc["is_major_flood_event"] == True]["record_date"].unique()
        flood_window_dates = set([d + pd.Timedelta(days=i) for d in flood_dates for i in range(6)])

        test_mask = (merged["state_code"] == "STC") & (merged["record_date"].isin(flood_window_dates))
        df_test = merged[test_mask]

        df_a = merged[merged["state_code"] == "STA"]
        df_b = merged[merged["state_code"] == "STB"]
        df_c_train = merged[(merged["state_code"] == "STC") & (~merged["record_date"].isin(flood_window_dates))]

        # Feature normalization
        mean_feat = df_a[self.feature_names].mean().to_numpy()
        std_feat = df_a[self.feature_names].std().to_numpy() + 1e-5

        def norm_X(df: pd.DataFrame) -> np.ndarray:
            return ((df[self.feature_names].to_numpy(dtype=np.float32) - mean_feat) / std_feat).astype(np.float32)

        return {
            "client_A": (norm_X(df_a), df_a["diarrhoeal_cases"].to_numpy(dtype=np.float32)),
            "client_B": (norm_X(df_b), df_b["diarrhoeal_cases"].to_numpy(dtype=np.float32)),
            "client_C_train": (norm_X(df_c_train), df_c_train["diarrhoeal_cases"].to_numpy(dtype=np.float32)),
            "client_C_test": (norm_X(df_test), df_test["diarrhoeal_cases"].to_numpy(dtype=np.float32)),
        }

    def train_and_compare(self, num_rounds: int = 10, local_epochs: int = 15, lr: float = 0.02) -> Dict[str, Any]:
        """Execute FedAvg across State A, B, C for 10 rounds,
        compare against Local and Centralized baselines on held-out State C high-rain flood events.
        """
        data = self.load_prepared_datasets()
        X_A, y_A = data["client_A"]
        X_B, y_B = data["client_B"]
        X_C_tr, y_C_tr = data["client_C_train"]
        X_test, y_test = data["client_C_test"]

        regressor = LinearUpliftRegressor(input_dim=self.input_dim, seed=self.seed)
        param_count = regressor.weights.parameter_count

        total_epochs = num_rounds * local_epochs

        # -------------------------------------------------------------
        # 1. LOCAL MODEL: Trained solely on State C normal history
        # -------------------------------------------------------------
        w_local = regressor.weights.copy()
        for _ in range(total_epochs):
            w_local = regressor.train_epoch(X_C_tr, y_C_tr, lr=lr, weights=w_local)

        y_pred_local = regressor.predict(X_test, weights=w_local)
        mae_local = float(np.mean(np.abs(y_pred_local - y_test)))

        # -------------------------------------------------------------
        # 2. CENTRALIZED MODEL: Pooled data from all three states
        # -------------------------------------------------------------
        X_central = np.vstack([X_A, X_B, X_C_tr])
        y_central = np.concatenate([y_A, y_B, y_C_tr])

        w_central = regressor.weights.copy()
        for _ in range(total_epochs):
            w_central = regressor.train_epoch(X_central, y_central, lr=lr, weights=w_central)

        y_pred_central = regressor.predict(X_test, weights=w_central)
        mae_central = float(np.mean(np.abs(y_pred_central - y_test)))

        # -------------------------------------------------------------
        # 3. FEDERATED MODEL: FedAvg across State A, B, and C
        # -------------------------------------------------------------
        clients = [
            ("State_A", X_A, y_A, len(X_A)),
            ("State_B", X_B, y_B, len(X_B)),
            ("State_C", X_C_tr, y_C_tr, len(X_C_tr)),
        ]
        total_samples = sum(c[3] for c in clients)

        w_global = regressor.weights.copy()
        convergence: List[Dict[str, Any]] = []

        for r in range(1, num_rounds + 1):
            local_client_weights = []

            # Client local training
            for _, X_k, y_k, _ in clients:
                cw = w_global.copy()
                for _ in range(local_epochs):
                    cw = regressor.train_epoch(X_k, y_k, lr=lr, weights=cw)
                local_client_weights.append(cw)

            # FedAvg: theta_global = sum (n_k / N) * theta_k
            agg_coef = np.zeros_like(w_global.coef)
            agg_intercept = 0.0

            for idx, (_, _, _, n_k) in enumerate(clients):
                fraction = n_k / total_samples
                cw = local_client_weights[idx]
                agg_coef += fraction * cw.coef
                agg_intercept += fraction * cw.intercept

            w_global = FederatedModelWeights(coef=agg_coef, intercept=agg_intercept)

            # Evaluate on held-out flood events from State C
            y_pred_r = regressor.predict(X_test, weights=w_global)
            mae_r = float(np.mean(np.abs(y_pred_r - y_test)))

            convergence.append({
                "round": r,
                "test_mae_state_c_flood": round(mae_r, 4),
            })

        y_pred_fed_final = regressor.predict(X_test, weights=w_global)
        mae_fed = float(np.mean(np.abs(y_pred_fed_final - y_test)))

        return {
            "simulation_result": True,
            "disclaimer": "Simulation result. Transparent FedAvg parameter averaging without raw row sharing. Do not claim formal differential privacy guarantees.",
            "task": "Rainfall Features -> Diarrhoeal Demand Uplift",
            "eval_cohort": "State C Held-Out High-Rain / Flood Disruption Events (144 facility-days)",
            "test_samples_count": len(X_test),
            "rounds": num_rounds,
            "local_epochs_per_round": local_epochs,
            "parameter_count": param_count,
            "features": self.feature_names,
            "clients": [
                {"client": "State_A", "samples": len(X_A), "history": "18 months"},
                {"client": "State_B", "samples": len(X_B), "history": "12 months"},
                {"client": "State_C", "samples": len(X_C_tr), "history": "18 months (normal periods only)"},
            ],
            "results": {
                "local": {
                    "strategy": "Local (State C normal data only, 0 cross-state pattern transfer)",
                    "mae": round(mae_local, 4),
                },
                "centralized": {
                    "strategy": "Centralized (Pooled raw data across all states)",
                    "mae": round(mae_central, 4),
                },
                "federated": {
                    "strategy": "Federated FedAvg (Zero raw data transfer, 10 rounds)",
                    "mae": round(mae_fed, 4),
                    "improvement_over_local_pct": round(((mae_local - mae_fed) / mae_local) * 100, 2),
                },
            },
            "convergence": convergence,
        }
