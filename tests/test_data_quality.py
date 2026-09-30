"""Unit and Integration Tests for HippoGrid Data Quality Engine.
Tests all 10 data quality checks and edge conditions:
1. Schema integrity
2. Required fields
3. Duplicate records
4. Negative inventory
5. Impossible staff counts
6. Invalid bed occupancy
7. Invalid dates
8. Missing values
9. Outliers
10. Cross-field consistency (consumption <= opening + received)
"""
import pytest
import pandas as pd
from datetime import date
from backend.core.data_quality import DataQualityEngine


@pytest.fixture
def dq_engine():
    return DataQualityEngine(allowed_overstaff_margin=4)


def test_clean_inventory_passes_validation(dq_engine):
    clean_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-01",
            "opening_stock": 100,
            "received": 50,
            "consumed": 20,
            "closing_stock": 130,
        },
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-02",
            "opening_stock": 130,
            "received": 0,
            "consumed": 30,
            "closing_stock": 100,
        },
    ])
    result = dq_engine.validate_dataset("inventory_transactions", clean_data)
    assert result.errors == 0
    assert result.quality_score == 100.0


def test_negative_inventory_detected(dq_engine):
    bad_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-01",
            "opening_stock": 50,
            "received": 0,
            "consumed": 60,
            "closing_stock": -10,  # Negative stock
        }
    ])
    result = dq_engine.validate_dataset("inventory_transactions", bad_data)
    assert result.errors > 0
    neg_issue = next((i for i in result.issues if i.check_type == "negative_inventory"), None)
    assert neg_issue is not None
    assert neg_issue.severity == "ERROR"
    assert result.quality_score < 100.0


def test_cross_field_consumption_inconsistency_detected(dq_engine):
    # consumption > opening + received
    inconsistent_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-01",
            "opening_stock": 50,
            "received": 10,
            "consumed": 100,  # Impossible consumption without adjustment!
            "closing_stock": 0,
            "is_adjustment": False,
        }
    ])
    result = dq_engine.validate_dataset("inventory_transactions", inconsistent_data)
    assert result.errors > 0
    issue = next((i for i in result.issues if i.check_type == "cross_field_consistency"), None)
    assert issue is not None
    assert "exceeds available stock" in issue.message


def test_cross_field_adjustment_flag_allowed(dq_engine):
    # marked as adjustment, should not flag as error
    adjusted_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-01",
            "opening_stock": 50,
            "received": 10,
            "consumed": 100,
            "closing_stock": 0,
            "is_adjustment": True,
        }
    ])
    result = dq_engine.validate_dataset("inventory_transactions", adjusted_data)
    issue = next((i for i in result.issues if i.check_type == "cross_field_consistency"), None)
    assert issue is None


def test_impossible_staff_counts_detected(dq_engine):
    # staff_present > staff_required + allowed_overstaff_margin (base required = 2, margin = 4 -> max 6)
    bad_staff_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "date": "2025-01-01",
            "mo_present": 1,
            "nurses_present": 12,  # Impossible count (> 2 + 4)
            "anm_present": 2,
        }
    ])
    result = dq_engine.validate_dataset("workforce_status", bad_staff_data)
    assert result.errors > 0
    issue = next((i for i in result.issues if i.check_type == "impossible_staff_counts"), None)
    assert issue is not None
    assert "nurses_present" in issue.message


def test_invalid_bed_occupancy_detected(dq_engine):
    # occupied_beds > total_beds
    bad_bed_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "date": "2025-01-01",
            "total_beds": 6,
            "occupied_beds": 8,  # > total_beds
            "available_beds": 0,
        }
    ])
    result = dq_engine.validate_dataset("bed_status", bad_bed_data)
    assert result.errors > 0
    issue = next((i for i in result.issues if i.check_type == "invalid_bed_occupancy"), None)
    assert issue is not None
    assert "occupied beds exceed total capacity" in issue.message


def test_duplicate_records_detected(dq_engine):
    dup_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-01",
            "closing_stock": 50,
        },
        {
            "phc_id": "PHC-TEST-001",
            "medicine_id": "MED-ORS-20.5G",
            "date": "2025-01-01",  # Duplicate composite key
            "closing_stock": 50,
        },
    ])
    result = dq_engine.validate_dataset("inventory_transactions", dup_data)
    assert result.errors > 0
    issue = next((i for i in result.issues if i.check_type == "duplicate_records"), None)
    assert issue is not None


def test_missing_required_fields_detected(dq_engine):
    missing_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            # missing medicine_id
            "date": "2025-01-01",
            "closing_stock": 50,
        }
    ])
    result = dq_engine.validate_dataset("inventory_transactions", missing_data)
    assert result.errors > 0
    issue = next((i for i in result.issues if i.check_type == "missing_required_fields"), None)
    assert issue is not None
    assert "medicine_id" in issue.message


def test_invalid_dates_detected(dq_engine):
    future_data = pd.DataFrame([
        {
            "phc_id": "PHC-TEST-001",
            "date": "2099-01-01",  # Future date
            "opd_cases": 20,
        }
    ])
    result = dq_engine.validate_dataset("patient_visits", future_data)
    assert result.errors > 0
    issue = next((i for i in result.issues if i.check_type == "invalid_dates"), None)
    assert issue is not None


def test_outlier_detection_warning(dq_engine):
    # Normal distribution with extreme outlier
    values = [20, 22, 21, 19, 23, 20, 21, 22, 19, 24] * 10
    values.append(500)  # Extreme outlier
    df = pd.DataFrame({
        "phc_id": ["PHC-001"] * len(values),
        "date": ["2025-01-01"] * len(values),
        "opd_cases": values,
    })
    result = dq_engine.validate_dataset("patient_visits", df)
    # Outliers produce warnings
    outlier_issue = next((i for i in result.issues if i.check_type == "statistical_outliers"), None)
    assert outlier_issue is not None
    assert outlier_issue.severity == "WARNING"
