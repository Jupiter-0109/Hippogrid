"""Tests for HippoGrid Phase 2 Synthetic Data Engine.
Validates network topology, dates, inventory guarantees, missing values, outliers,
flood counts, and deterministic reproducibility.
"""
from datetime import date
import numpy as np
import pandas as pd
import pytest

from backend.sim.generator import SyntheticDataGenerator
from backend.sim.network import build_network_topology


@pytest.fixture(scope="module")
def generated_data():
    """Module-level fixture to run generator once with seed 42."""
    generator = SyntheticDataGenerator(seed=42)
    return generator.generate_all()


# =============================================================================
# 1. Exact Count Tests: States, Districts, PHCs, Warehouses
# =============================================================================

def test_exact_state_count(generated_data):
    """Verify exact state count is 3."""
    df_states = generated_data["states"]
    assert len(df_states) == 3
    assert set(df_states["code"]) == {"STA", "STB", "STC"}


def test_exact_district_count(generated_data):
    """Verify exact district count is 6 (2 per state)."""
    df_districts = generated_data["districts"]
    assert len(df_districts) == 6
    # Each state must have exactly 2 districts
    state_counts = df_districts["state_code"].value_counts().to_dict()
    assert state_counts == {"STA": 2, "STB": 2, "STC": 2}


def test_exact_phc_count(generated_data):
    """Verify exact PHC count is 36 (6 per district)."""
    df_phcs = generated_data["phcs"]
    assert len(df_phcs) == 36
    # Each district must have exactly 6 PHCs
    dist_counts = df_phcs["district_code"].value_counts().to_dict()
    assert len(dist_counts) == 6
    assert all(count == 6 for count in dist_counts.values())


def test_exact_warehouse_count(generated_data):
    """Verify exact warehouse count is 6 (1 per district)."""
    df_warehouses = generated_data["warehouses"]
    assert len(df_warehouses) == 6


# =============================================================================
# 2. Date Constraints & State B Start Date
# =============================================================================

def test_state_b_date_start(generated_data):
    """Verify State B records strictly begin on 2024-07-01 (12 months)."""
    df_weather = generated_data["weather"]
    state_b_weather = df_weather[df_weather["state_code"] == "STB"]
    
    min_date_b = state_b_weather["record_date"].min()
    max_date_b = state_b_weather["record_date"].max()
    assert min_date_b == date(2024, 7, 1)
    assert max_date_b == date(2025, 6, 30)

    # State A and C must span full 18 months from 2024-01-01
    state_a_weather = df_weather[df_weather["state_code"] == "STA"]
    assert state_a_weather["record_date"].min() == date(2024, 1, 1)
    assert state_a_weather["record_date"].max() == date(2025, 6, 30)


def test_valid_date_ranges_all_tables(generated_data):
    """Verify all telemetry tables only contain dates within [2024-01-01, 2025-06-30]."""
    start_bound = date(2024, 1, 1)
    end_bound = date(2025, 6, 30)

    for tbl_name in ["weather", "power", "patient_clean", "workforce", "beds", "inventory", "roads"]:
        df = generated_data[tbl_name]
        min_dt = df["record_date"].min()
        max_dt = df["record_date"].max()
        assert min_dt >= start_bound, f"{tbl_name} date before start bound: {min_dt}"
        assert max_dt <= end_bound, f"{tbl_name} date after end bound: {max_dt}"


# =============================================================================
# 3. State C Flood Event Invariant
# =============================================================================

def test_state_c_flood_event_count(generated_data):
    """Verify State C has lower disaster history with strictly exactly 2 major flood events."""
    df_weather = generated_data["weather"]
    state_c_weather = df_weather[df_weather["state_code"] == "STC"]
    
    # Count rows where is_major_flood_event is True
    flood_events = state_c_weather[state_c_weather["is_major_flood_event"] == True]
    assert len(flood_events) == 2, f"Expected 2 flood events in State C, got {len(flood_events)}"

    # Ensure other states have higher disaster history (> 2)
    state_a_floods = df_weather[(df_weather["state_code"] == "STA") & (df_weather["is_major_flood_event"] == True)]
    assert len(state_a_floods) > 2


# =============================================================================
# 4. Inventory Continuity & Zero Negative Stock Invariant
# =============================================================================

def test_no_invalid_negative_stock(generated_data):
    """Verify that closing stock and opening stock are NEVER negative in any facility."""
    df_inv = generated_data["inventory"]
    
    # Assert no negative values
    assert (df_inv["opening_stock"] >= 0).all(), "Found negative opening stock"
    assert (df_inv["received"] >= 0).all(), "Found negative received stock"
    assert (df_inv["consumed"] >= 0).all(), "Found negative consumed stock"
    assert (df_inv["closing_stock"] >= 0).all(), "Found negative closing stock"

    # Verify continuity equation: closing = opening + received - consumed
    calc_closing = df_inv["opening_stock"] + df_inv["received"] - df_inv["consumed"]
    diff = np.abs(df_inv["closing_stock"] - calc_closing)
    assert (diff < 1e-2).all(), "Stock continuity balance broken"


# =============================================================================
# 5. Missing-Value Percentage
# =============================================================================

def test_missing_value_percentage(generated_data):
    """Verify realistic missing values are injected within a controlled 1.0% to 3.0% range."""
    # Check patient table opd_cases
    df_patient = generated_data["patient"]
    opd_null_pct = (df_patient["opd_cases"].isna().sum() / len(df_patient)) * 100.0
    assert 1.0 <= opd_null_pct <= 3.0, f"OPD missing percentage out of range: {opd_null_pct}%"

    # Check weather rainfall_mm
    df_weather = generated_data["weather"]
    rain_null_pct = (df_weather["rainfall_mm"].isna().sum() / len(df_weather)) * 100.0
    assert 1.0 <= rain_null_pct <= 3.0, f"Weather missing percentage out of range: {rain_null_pct}%"

    # Check power outage_hours
    df_power = generated_data["power"]
    outage_null_pct = (df_power["outage_hours"].isna().sum() / len(df_power)) * 100.0
    assert 1.0 <= outage_null_pct <= 3.0, f"Power missing percentage out of range: {outage_null_pct}%"


# =============================================================================
# 6. Outlier Detection
# =============================================================================

def test_outlier_detection(generated_data):
    """Verify that clinical and weather outliers exist and are detectable via statistical Z-scores."""
    df_clean = generated_data["patient_clean"]
    
    # Specifically check the injected acute gastroenteritis outbreak at PHC-DST-A1-05
    phc_series = df_clean[df_clean["phc_code"] == "PHC-DST-A1-05"]["diarrhoeal_cases"]
    mean = phc_series.mean()
    std = phc_series.std()
    z_scores = (phc_series - mean) / std

    outlier_max_z = z_scores.max()
    assert outlier_max_z > 4.0, f"Expected outbreak outlier Z-score > 4.0, got {outlier_max_z}"

    # Verify dengue fever cluster outlier at PHC-DST-B1-02
    phc_fever = df_clean[df_clean["phc_code"] == "PHC-DST-B1-02"]["fever_cases"]
    z_fever = (phc_fever - phc_fever.mean()) / phc_fever.std()
    assert z_fever.max() > 4.0, f"Expected fever outbreak outlier Z-score > 4.0, got {z_fever.max()}"


# =============================================================================
# 7. Seed 42 Deterministic Reproducibility
# =============================================================================

def test_reproducibility():
    """Verify that instantiating two generators with seed 42 yields 100% identical telemetry."""
    gen1 = SyntheticDataGenerator(seed=42)
    gen2 = SyntheticDataGenerator(seed=42)

    data1 = gen1.generate_all()
    data2 = gen2.generate_all()

    # Compare clean patient telemetry
    pd.testing.assert_frame_equal(data1["patient_clean"], data2["patient_clean"])
    # Compare inventory telemetry
    pd.testing.assert_frame_equal(data1["inventory"], data2["inventory"])
    # Compare weather
    pd.testing.assert_series_equal(
        data1["weather"]["temperature_celsius"],
        data2["weather"]["temperature_celsius"],
    )
