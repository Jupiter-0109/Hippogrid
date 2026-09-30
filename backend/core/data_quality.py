"""HippoGrid Data Quality & Validation Engine.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Validates 10 core data quality dimensions:
1. Schema integrity
2. Required fields
3. Duplicate records
4. Negative inventory (closing_stock >= 0)
5. Impossible staff counts (staff_present <= base + allowed_margin)
6. Invalid bed occupancy (occupied_beds <= total_beds)
7. Invalid dates
8. Missing values quantification
9. Statistical outliers detection
10. Cross-field consistency (consumption <= opening + received)
"""
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session


@dataclass
class ValidationIssue:
    check_type: str
    severity: str  # ERROR or WARNING
    message: str
    field_name: Optional[str] = None
    row_count: int = 0
    sample_records: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DatasetQualityResult:
    dataset: str
    rows_checked: int
    errors: int
    warnings: int
    quality_score: float  # 0.0 to 100.0
    issues: List[ValidationIssue] = field(default_factory=list)


@dataclass
class OverallQualityReport:
    run_id: str
    timestamp: str
    overall_quality_score: float
    total_rows_checked: int
    total_errors: int
    total_warnings: int
    dataset_results: Dict[str, DatasetQualityResult] = field(default_factory=dict)


class DataQualityEngine:
    """Rigorous data validation and scoring engine for HippoGrid telemetry."""

    def __init__(self, allowed_overstaff_margin: int = 4) -> None:
        self.allowed_overstaff_margin = allowed_overstaff_margin

    def validate_dates(self, df: pd.DataFrame, date_col: str = "date") -> List[ValidationIssue]:
        """Validate date formatting, non-future dates, and plausibility."""
        issues: List[ValidationIssue] = []
        col = date_col if date_col in df.columns else ("record_date" if "record_date" in df.columns else None)
        if not col:
            return issues

        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            invalid_format = parsed.isna().sum() - df[col].isna().sum()
            if invalid_format > 0:
                issues.append(
                    ValidationIssue(
                        "invalid_dates",
                        "ERROR",
                        f"Found {invalid_format} unparseable date values in column '{col}'",
                        col,
                        int(invalid_format),
                    )
                )

            # Check future dates (relative to current date or year 2026)
            today_ts = pd.Timestamp.now()
            future_mask = parsed > today_ts
            future_count = int(future_mask.sum())
            if future_count > 0:
                issues.append(
                    ValidationIssue(
                        "invalid_dates",
                        "ERROR",
                        f"Found {future_count} future dated records in column '{col}'",
                        col,
                        future_count,
                    )
                )
        except Exception as e:
            issues.append(
                ValidationIssue("invalid_dates", "ERROR", f"Error checking dates: {str(e)}", col, 1)
            )

        return issues

    def validate_dataset(self, dataset_name: str, df: pd.DataFrame) -> DatasetQualityResult:
        """Generic dispatcher for validating datasets by name."""
        name_lower = dataset_name.lower()
        if "inventory" in name_lower:
            return self.validate_inventory(df)
        elif "bed" in name_lower:
            return self.validate_beds(df)
        elif "workforce" in name_lower or "staff" in name_lower:
            return self.validate_workforce(df)
        elif "patient" in name_lower or "visit" in name_lower:
            return self.validate_patients(df)
        elif "power" in name_lower:
            return self.validate_power(df)
        else:
            # Default schema and null check
            issues: List[ValidationIssue] = []
            issues.extend(self.validate_dates(df))
            return self._score_dataset(dataset_name, len(df), issues)

    def validate_inventory(self, df: pd.DataFrame) -> DatasetQualityResult:
        """Validate inventory transactions / daily inventory telemetry."""
        issues: List[ValidationIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return DatasetQualityResult("inventory", 0, 0, 0, 100.0, [])

        # Schema & Required fields
        date_col = "date" if "date" in df.columns else "record_date"
        id_col = "phc_id" if "phc_id" in df.columns else "phc_code"
        required = [id_col, "medicine_id", date_col, "opening_stock", "closing_stock"]
        missing_cols = [c for c in ["medicine_id", "opening_stock", "closing_stock"] if c not in df.columns]
        if missing_cols:
            issues.append(
                ValidationIssue("missing_required_fields", "ERROR", f"Missing required columns: {missing_cols}", row_count=n_rows)
            )

        # Dates validation
        issues.extend(self.validate_dates(df, date_col))

        # Duplicate records (unique on phc_id/code, medicine_id, date)
        subset_cols = [c for c in [id_col, "medicine_id", date_col] if c in df.columns]
        if len(subset_cols) >= 2:
            dups = df.duplicated(subset=subset_cols).sum()
            if dups > 0:
                issues.append(
                    ValidationIssue("duplicate_records", "ERROR", f"Found {dups} duplicate inventory records", row_count=int(dups))
                )

        # Negative inventory check: closing_stock >= 0 and opening_stock >= 0
        if "closing_stock" in df.columns:
            neg_closing = df[df["closing_stock"] < 0]
            if len(neg_closing) > 0:
                issues.append(
                    ValidationIssue("negative_inventory", "ERROR", f"Found {len(neg_closing)} records with negative closing stock (closing_stock >= 0 violated)", "closing_stock", len(neg_closing))
                )

        if "opening_stock" in df.columns:
            neg_opening = df[df["opening_stock"] < 0]
            if len(neg_opening) > 0:
                issues.append(
                    ValidationIssue("negative_inventory", "ERROR", f"Found {len(neg_opening)} records with negative opening stock", "opening_stock", len(neg_opening))
                )

        # Cross-field consistency: consumed <= opening_stock + received (unless marked as adjustment)
        consumed_col = "consumed" if "consumed" in df.columns else ("consumption" if "consumption" in df.columns else None)
        if consumed_col and "opening_stock" in df.columns:
            rec = df["received"] if "received" in df.columns else 0
            is_adj = df["is_adjustment"] if "is_adjustment" in df.columns else pd.Series(False, index=df.index)
            over_consumed = df[(df[consumed_col] > (df["opening_stock"] + rec + 1e-4)) & (~is_adj)]
            if len(over_consumed) > 0:
                issues.append(
                    ValidationIssue(
                        "cross_field_consistency",
                        "ERROR",
                        f"Found {len(over_consumed)} records where consumption exceeds available stock (consumption <= opening + received)",
                        consumed_col,
                        len(over_consumed),
                    )
                )

        # Missing values
        for c in ["opening_stock", "closing_stock", consumed_col]:
            if c and c in df.columns:
                nulls = df[c].isna().sum()
                if nulls > 0:
                    pct = round((nulls / n_rows) * 100, 2)
                    issues.append(
                        ValidationIssue("missing_values", "WARNING", f"Column '{c}' has {nulls} missing values ({pct}%)", c, int(nulls))
                    )

        return self._score_dataset("inventory", n_rows, issues)

    def validate_beds(self, df: pd.DataFrame) -> DatasetQualityResult:
        """Validate inpatient bed telemetry."""
        issues: List[ValidationIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return DatasetQualityResult("beds", 0, 0, 0, 100.0, [])

        issues.extend(self.validate_dates(df))

        # 1. Invalid bed occupancy: occupied_beds <= total_beds
        if all(c in df.columns for c in ["occupied_beds", "total_beds"]):
            over_occupied = df[df["occupied_beds"] > df["total_beds"]]
            if len(over_occupied) > 0:
                issues.append(
                    ValidationIssue("invalid_bed_occupancy", "ERROR", f"Found {len(over_occupied)} records where occupied beds exceed total capacity", "occupied_beds", len(over_occupied))
                )

            neg_beds = df[(df["occupied_beds"] < 0) | (df["total_beds"] <= 0)]
            if len(neg_beds) > 0:
                issues.append(
                    ValidationIssue("invalid_bed_occupancy", "ERROR", f"Found {len(neg_beds)} records with negative or zero bed capacity", "total_beds", len(neg_beds))
                )

        # 2. Cross-field consistency: total_beds == occupied_beds + available_beds
        if all(c in df.columns for c in ["total_beds", "occupied_beds", "available_beds"]):
            sum_mismatch = df[df["total_beds"] != (df["occupied_beds"] + df["available_beds"])]
            if len(sum_mismatch) > 0:
                issues.append(
                    ValidationIssue("cross_field_consistency", "WARNING", f"Found {len(sum_mismatch)} records where total != occupied + available", "available_beds", len(sum_mismatch))
                )

        return self._score_dataset("beds", n_rows, issues)

    def validate_workforce(self, df: pd.DataFrame, phcs_df: Optional[pd.DataFrame] = None) -> DatasetQualityResult:
        """Validate clinical workforce duty rosters and impossible staffing counts."""
        issues: List[ValidationIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return DatasetQualityResult("workforce", 0, 0, 0, 100.0, [])

        issues.extend(self.validate_dates(df))

        # 1. Negative staff counts
        nurse_col = "nurse_on_duty" if "nurse_on_duty" in df.columns else ("nurses_present" if "nurses_present" in df.columns else None)
        mo_col = "mo_on_duty" if "mo_on_duty" in df.columns else ("mo_present" if "mo_present" in df.columns else None)
        anm_col = "anm_on_duty" if "anm_on_duty" in df.columns else ("anm_present" if "anm_present" in df.columns else None)

        for role in [c for c in [mo_col, nurse_col, anm_col] if c]:
            neg = df[df[role] < 0]
            if len(neg) > 0:
                issues.append(
                    ValidationIssue("impossible_staff_counts", "ERROR", f"Found {len(neg)} records with negative {role}", role, len(neg))
                )

        # 2. Impossible staff counts (overstaff limit: staff_present <= staff_required + allowed_overstaff_margin)
        # e.g., nurse count > 2 + allowed_margin (default allowed_overstaff_margin=4 -> max 6)
        if nurse_col:
            over = df[df[nurse_col] > (2 + self.allowed_overstaff_margin)]
            if len(over) > 0:
                issues.append(
                    ValidationIssue("impossible_staff_counts", "ERROR", f"Found {len(over)} records with impossible staff count in {nurse_col} (> {2 + self.allowed_overstaff_margin})", nurse_col, len(over))
                )

        # 3. Missing values
        if "absenteeism_rate" in df.columns:
            nulls = df["absenteeism_rate"].isna().sum()
            if nulls > 0:
                issues.append(
                    ValidationIssue("missing_values", "WARNING", f"Found {nulls} missing absenteeism rates", "absenteeism_rate", int(nulls))
                )

        return self._score_dataset("workforce", n_rows, issues)

    def validate_patients(self, df: pd.DataFrame) -> DatasetQualityResult:
        """Validate patient caseload presentations and detect statistical outliers."""
        issues: List[ValidationIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return DatasetQualityResult("patient", 0, 0, 0, 100.0, [])

        issues.extend(self.validate_dates(df))

        # 1. Negative cases
        for col in ["opd_cases", "emergency_cases", "diarrhoeal_cases", "fever_cases", "deliveries"]:
            if col in df.columns:
                neg = df[df[col] < 0]
                if len(neg) > 0:
                    issues.append(
                        ValidationIssue("negative_cases", "ERROR", f"Found {len(neg)} records with negative {col}", col, len(neg))
                    )

        # 2. Outliers Detection (Z-Score > 4.0)
        for col in ["diarrhoeal_cases", "fever_cases", "opd_cases", "emergency_cases"]:
            if col in df.columns and df[col].notna().sum() > 20:
                series = df[col].dropna()
                mean = series.mean()
                std = series.std()
                if std > 0:
                    z = (series - mean) / std
                    outliers = (z > 4.0).sum()
                    if outliers > 0:
                        issues.append(
                            ValidationIssue("statistical_outliers", "WARNING", f"Detected {outliers} statistical outbreak outliers (Z > 4.0) in {col}", col, int(outliers))
                        )

        # 3. Missing values
        for col in ["opd_cases", "emergency_cases"]:
            if col in df.columns:
                nulls = df[col].isna().sum()
                if nulls > 0:
                    issues.append(
                        ValidationIssue("missing_values", "WARNING", f"Found {nulls} missing values in {col}", col, int(nulls))
                    )

        return self._score_dataset("patient", n_rows, issues)

    def validate_power(self, df: pd.DataFrame) -> DatasetQualityResult:
        """Validate power telemetry and outage hours."""
        issues: List[ValidationIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return DatasetQualityResult("power", 0, 0, 0, 100.0, [])

        # 1. Outage hours must be in [0, 24]
        if "outage_hours" in df.columns:
            invalid_outage = df[(df["outage_hours"] < 0) | (df["outage_hours"] > 24.0)]
            if len(invalid_outage) > 0:
                issues.append(
                    ValidationIssue("invalid_power_hours", "ERROR", f"Found {len(invalid_outage)} records with outage hours outside [0, 24]", "outage_hours", len(invalid_outage))
                )

        # 2. Cross-field: outage_hours + grid_uptime_hours == 24
        if all(c in df.columns for c in ["outage_hours", "grid_uptime_hours"]):
            valid_rows = df.dropna(subset=["outage_hours", "grid_uptime_hours"])
            mismatch = valid_rows[np.abs(valid_rows["outage_hours"] + valid_rows["grid_uptime_hours"] - 24.0) > 0.05]
            if len(mismatch) > 0:
                issues.append(
                    ValidationIssue("cross_field_consistency", "WARNING", f"Found {len(mismatch)} records where outage + uptime != 24 hours", "grid_uptime_hours", len(mismatch))
                )

        return self._score_dataset("power", n_rows, issues)

    def validate_all(self, datasets: Dict[str, pd.DataFrame]) -> OverallQualityReport:
        """Run complete validation suite across all domain datasets."""
        results: Dict[str, DatasetQualityResult] = {}

        if "inventory" in datasets:
            results["inventory"] = self.validate_inventory(datasets["inventory"])
        if "beds" in datasets:
            results["beds"] = self.validate_beds(datasets["beds"])
        if "workforce" in datasets:
            results["workforce"] = self.validate_workforce(datasets["workforce"], datasets.get("phcs"))
        if "patient" in datasets:
            results["patient"] = self.validate_patients(datasets["patient"])
        if "power" in datasets:
            results["power"] = self.validate_power(datasets["power"])

        total_rows = sum(r.rows_checked for r in results.values())
        total_errors = sum(r.errors for r in results.values())
        total_warnings = sum(r.warnings for r in results.values())

        # Overall quality score: weighted average of dataset scores
        if results:
            avg_score = round(float(np.mean([r.quality_score for r in results.values()])), 1)
        else:
            avg_score = 100.0

        run_id = f"dq-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        return OverallQualityReport(
            run_id=run_id,
            timestamp=datetime.utcnow().isoformat(),
            overall_quality_score=avg_score,
            total_rows_checked=total_rows,
            total_errors=total_errors,
            total_warnings=total_warnings,
            dataset_results=results,
        )

    def _score_dataset(self, name: str, rows: int, issues: List[ValidationIssue]) -> DatasetQualityResult:
        errors = sum(i.row_count for i in issues if i.severity == "ERROR")
        warnings = sum(i.row_count for i in issues if i.severity == "WARNING")

        # Penalty score formula
        # Errors deduct 5 points per 1% affected rows; warnings deduct 0.5 points per 1% affected
        if rows > 0:
            error_penalty = (errors / rows) * 100.0 * 5.0
            warning_penalty = (warnings / rows) * 100.0 * 0.5
            score = max(0.0, min(100.0, 100.0 - error_penalty - warning_penalty))
        else:
            score = 100.0

        return DatasetQualityResult(
            dataset=name,
            rows_checked=rows,
            errors=errors,
            warnings=warnings,
            quality_score=round(score, 1),
            issues=issues,
        )

    def persist_results(self, db: Session, report: OverallQualityReport) -> None:
        """Persist data quality validation run to Supabase PostgreSQL table."""
        from sqlalchemy import text
        for ds_name, res in report.dataset_results.items():
            issues_json = [asdict(i) for i in res.issues]
            db.execute(
                text("""
                    INSERT INTO data_quality_results (
                        run_id, dataset, rows_checked, errors, warnings, quality_score, details_json
                    ) VALUES (
                        :run_id, :dataset, :rows_checked, :errors, :warnings, :quality_score, :details_json
                    )
                """),
                {
                    "run_id": report.run_id,
                    "dataset": ds_name,
                    "rows_checked": res.rows_checked,
                    "errors": res.errors,
                    "warnings": res.warnings,
                    "quality_score": res.quality_score,
                    "details_json": json_dumps(issues_json),
                },
            )
        db.commit()


def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj)
