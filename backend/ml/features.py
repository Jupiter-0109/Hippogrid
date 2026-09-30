"""Feature Engineering Pipeline for HippoGrid Demand & Caseload Forecasting.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Targets:
- diarrhoeal_cases
- fever_cases
- medicine_consumption (e.g. ORS, zinc, paracetamol, etc.)

Features created:
- lag_1, lag_3, lag_7, lag_14
- rolling_mean_7, rolling_mean_14
- day_of_week, month
- rainfall, rainfall_lag_1, rainfall_lag_2, rainfall_lag_3, rainfall_lag_4
- population_served (catchment_population)
- remote_flag (0/1)
- state_id (encoded / categorical)

Strict time-series split to prevent data leakage:
- 60% training
- 20% calibration
- 20% testing
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.core.config import PROJECT_ROOT

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


@dataclass
class DatasetSplits:
    X_train: pd.DataFrame
    y_train: pd.Series
    X_cal: pd.DataFrame
    y_cal: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    df_train: pd.DataFrame
    df_cal: pd.DataFrame
    df_test: pd.DataFrame
    feature_names: List[str]
    target_col: str


class FeaturePipeline:
    """Extracts features, prevents data leakage via temporal sorting, and performs 60/20/20 split."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or RAW_DATA_DIR
        self.feature_columns = [
            "lag_1",
            "lag_3",
            "lag_7",
            "lag_14",
            "rolling_mean_7",
            "rolling_mean_14",
            "day_of_week",
            "month",
            "rainfall",
            "rainfall_lag_1",
            "rainfall_lag_2",
            "rainfall_lag_3",
            "rainfall_lag_4",
            "population_served",
            "remote_flag",
            "state_id",
        ]

    def load_telemetry(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load raw or parquet telemetry datasets."""
        # PHCs
        phcs_path = self.data_dir / "phcs.parquet" if (self.data_dir / "phcs.parquet").exists() else self.data_dir / "phcs.csv"
        df_phcs = pd.read_parquet(phcs_path) if str(phcs_path).endswith(".parquet") else pd.read_csv(phcs_path)

        # Weather
        w_path = self.data_dir / "weather.parquet" if (self.data_dir / "weather.parquet").exists() else self.data_dir / "weather.csv"
        df_weather = pd.read_parquet(w_path) if str(w_path).endswith(".parquet") else pd.read_csv(w_path)

        # Patients
        pt_path = self.data_dir / "patient.parquet" if (self.data_dir / "patient.parquet").exists() else self.data_dir / "patient.csv"
        df_patients = pd.read_parquet(pt_path) if str(pt_path).endswith(".parquet") else pd.read_csv(pt_path)

        # Inventory
        inv_path = self.data_dir / "inventory.parquet" if (self.data_dir / "inventory.parquet").exists() else self.data_dir / "inventory.csv"
        df_inventory = pd.read_parquet(inv_path) if str(inv_path).endswith(".parquet") else pd.read_csv(inv_path)

        return df_phcs, df_weather, df_patients, df_inventory

    def build_weather_features(self, df_weather: pd.DataFrame) -> pd.DataFrame:
        """Create rainfall lag features on weather dataframe."""
        df_w = df_weather.copy()
        df_w["record_date"] = pd.to_datetime(df_w["record_date"])
        df_w = df_w.sort_values(["district_code", "record_date"]).reset_index(drop=True)

        # Rainfall lags per district
        df_w["rainfall"] = df_w["rainfall_mm"].fillna(0.0)
        for lag in [1, 2, 3, 4]:
            df_w[f"rainfall_lag_{lag}"] = df_w.groupby("district_code")["rainfall"].shift(lag).fillna(0.0)

        return df_w[["district_code", "record_date", "rainfall", "rainfall_lag_1", "rainfall_lag_2", "rainfall_lag_3", "rainfall_lag_4"]]

    def build_dataset_for_target(
        self,
        target_name: str,
        medicine_id: Optional[str] = "ORS",
    ) -> pd.DataFrame:
        """Build feature matrix for target: 'diarrhoeal_cases', 'fever_cases', or 'medicine_consumption'."""
        df_phcs, df_weather, df_patients, df_inventory = self.load_telemetry()

        # PHC lookup map
        phc_meta = df_phcs[["code", "district_code", "state_code", "catchment_population", "remote_flag"]].copy()
        phc_meta = phc_meta.rename(
            columns={
                "code": "phc_code",
                "catchment_population": "population_served",
            }
        )
        # Remote flag to int (0/1)
        phc_meta["remote_flag"] = phc_meta["remote_flag"].astype(int)

        # Map state_code to integer code
        state_map = {sc: idx for idx, sc in enumerate(sorted(phc_meta["state_code"].unique()))}
        phc_meta["state_id"] = phc_meta["state_code"].map(state_map)

        # Weather features
        df_w_feats = self.build_weather_features(df_weather)

        # Choose primary timeseries
        if target_name in ["diarrhoeal_cases", "fever_cases"]:
            ts_df = df_patients[["phc_code", "record_date", target_name]].copy()
            ts_df["target"] = ts_df[target_name].astype(float)
        elif target_name == "medicine_consumption":
            inv_sub = df_inventory[df_inventory["medicine_id"] == medicine_id].copy()
            ts_df = inv_sub[["phc_code", "record_date", "consumed"]].copy()
            ts_df["target"] = ts_df["consumed"].astype(float)
        else:
            raise ValueError(f"Unknown target: {target_name}")

        ts_df["record_date"] = pd.to_datetime(ts_df["record_date"])
        # Merge PHC metadata
        merged = ts_df.merge(phc_meta, on="phc_code", how="inner")
        # Merge weather
        merged = merged.merge(df_w_feats, on=["district_code", "record_date"], how="left")

        # Fill rainfall if missing
        for col in ["rainfall", "rainfall_lag_1", "rainfall_lag_2", "rainfall_lag_3", "rainfall_lag_4"]:
            merged[col] = merged[col].fillna(0.0)

        # Sort strictly chronologically by facility and date
        merged = merged.sort_values(["phc_code", "record_date"]).reset_index(drop=True)

        # Temporal features
        merged["day_of_week"] = merged["record_date"].dt.dayofweek
        merged["month"] = merged["record_date"].dt.month

        # Group-wise lags and rolling statistics (per PHC)
        grouped = merged.groupby("phc_code")["target"]

        # Lags
        merged["lag_1"] = grouped.shift(1)
        merged["lag_3"] = grouped.shift(3)
        merged["lag_7"] = grouped.shift(7)
        merged["lag_14"] = grouped.shift(14)

        # Rolling means (strictly shifted to prevent data leakage of current day)
        merged["rolling_mean_7"] = grouped.transform(lambda s: s.shift(1).rolling(window=7, min_periods=3).mean())
        merged["rolling_mean_14"] = grouped.transform(lambda s: s.shift(1).rolling(window=14, min_periods=7).mean())

        # Baseline comparative predictors (no leakage)
        # 1. Same weekday previous week = lag_7
        merged["baseline_same_weekday_prev_week"] = merged["lag_7"]
        # 2. 7-day moving average = rolling_mean_7
        merged["baseline_7day_moving_avg"] = merged["rolling_mean_7"]

        # Drop initial rows with NaN from lag_14
        valid_df = merged.dropna(subset=["lag_14", "rolling_mean_14", "target"]).copy()
        # Sort by record_date globally to guarantee temporal integrity across facilities
        valid_df = valid_df.sort_values(["record_date", "phc_code"]).reset_index(drop=True)

        return valid_df

    def split_data(self, df: pd.DataFrame, train_ratio: float = 0.60, cal_ratio: float = 0.20) -> DatasetSplits:
        """Strict time-based split: 60% Train, 20% Calibration, 20% Test."""
        unique_dates = np.sort(df["record_date"].unique())
        n_dates = len(unique_dates)

        train_cutoff_idx = int(n_dates * train_ratio)
        cal_cutoff_idx = int(n_dates * (train_ratio + cal_ratio))

        train_date_end = unique_dates[train_cutoff_idx]
        cal_date_end = unique_dates[cal_cutoff_idx]

        train_mask = df["record_date"] < train_date_end
        cal_mask = (df["record_date"] >= train_date_end) & (df["record_date"] < cal_date_end)
        test_mask = df["record_date"] >= cal_date_end

        df_train = df[train_mask].copy()
        df_cal = df[cal_mask].copy()
        df_test = df[test_mask].copy()

        X_train = df_train[self.feature_columns]
        y_train = df_train["target"]

        X_cal = df_cal[self.feature_columns]
        y_cal = df_cal["target"]

        X_test = df_test[self.feature_columns]
        y_test = df_test["target"]

        return DatasetSplits(
            X_train=X_train,
            y_train=y_train,
            X_cal=X_cal,
            y_cal=y_cal,
            X_test=X_test,
            y_test=y_test,
            df_train=df_train,
            df_cal=df_cal,
            df_test=df_test,
            feature_names=self.feature_columns,
            target_col="target",
        )
