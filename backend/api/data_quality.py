"""Data Quality API endpoints for HippoGrid."""
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Depends
import pandas as pd
from sqlalchemy.orm import Session
from backend.core.config import PROJECT_ROOT
from backend.core.data_quality import DataQualityEngine
from backend.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["data-quality"])
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


@router.get("/data-quality")
def get_data_quality(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return comprehensive data quality metrics across all telemetry domains."""
    engine = DataQualityEngine()

    # Load telemetry datasets from raw storage or database
    datasets: Dict[str, pd.DataFrame] = {}
    for name in ["inventory", "beds", "workforce", "patient", "power"]:
        csv_file = RAW_DATA_DIR / f"{name}.csv"
        parquet_file = RAW_DATA_DIR / f"{name}.parquet"
        if parquet_file.exists():
            datasets[name] = pd.read_parquet(parquet_file)
        elif csv_file.exists():
            datasets[name] = pd.read_csv(csv_file)

    report = engine.validate_all(datasets)

    # Status classification
    if report.overall_quality_score >= 95.0:
        quality_status = "HEALTHY"
    elif report.overall_quality_score >= 85.0:
        quality_status = "WARNING"
    else:
        quality_status = "CRITICAL"

    return {
        "run_id": report.run_id,
        "timestamp": report.timestamp,
        "overall_quality_score": report.overall_quality_score,
        "quality_status": quality_status,
        "total_rows_checked": report.total_rows_checked,
        "total_errors": report.total_errors,
        "total_warnings": report.total_warnings,
        "datasets": {
            name: {
                "rows_checked": res.rows_checked,
                "errors": res.errors,
                "warnings": res.warnings,
                "quality_score": res.quality_score,
                "issues": [
                    {
                        "check_type": i.check_type,
                        "severity": i.severity,
                        "message": i.message,
                        "field_name": i.field_name,
                        "row_count": i.row_count,
                    }
                    for i in res.issues
                ],
            }
            for name, res in report.dataset_results.items()
        },
    }
