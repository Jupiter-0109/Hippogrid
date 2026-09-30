"""Unit and Hand-Calculated Verification Tests for HippoGrid SCH Engine.
Service-Capability Graph & Horizon Calculator tests.

Includes mandatory hand-calculated examples:
1. stock = 100, demand = 2/hour -> drug horizon = 50.0 hours
2. road closure (BLOCKED) stops replenishment buffer
3. status thresholds: HEALTHY (>=72h), WATCH (48h-72h), CRITICAL (<48h)
4. limiting dependency identification (minimum horizon dependency)
5. next limiting dependency identification
"""
import pytest
from backend.sch.service_graph import ServiceCapabilityGraph
from backend.sch.horizon import (
    ServiceCapabilityHorizonCalculator,
    ServiceCapabilityAssessment,
    DependencyHorizon,
)


@pytest.fixture
def sch_calculator():
    graph = ServiceCapabilityGraph()
    return ServiceCapabilityHorizonCalculator(graph=graph)


# ==============================================================================
# MANDATORY HAND-CALCULATED EXAMPLES FROM USER SPECIFICATION
# ==============================================================================

def test_hand_calculated_drug_depletion_50_hours(sch_calculator):
    """Spec Requirement:
    stock = 100
    demand = 2/hour
    drug horizon = 50 hours
    """
    stock = 100.0
    demand_per_hour = 2.0
    drug_horizon = sch_calculator.calculate_drug_horizon(stock=stock, demand_per_hour=demand_per_hour)
    
    assert drug_horizon == 50.0, f"Expected 50.0 hours, got {drug_horizon}"


def test_hand_calculated_road_closure_impact(sch_calculator):
    """Spec Requirement:
    If road closure blocks replenishment, the calculation must reflect that.
    When road_status is BLOCKED:
    1. calculate_road_access_horizon returns 0.0h.
    2. compute_sch reflects road blockage and identifies limiting dependency.
    """
    # Road blocked gives immediate 0.0 hour logistics buffer
    road_horizon = sch_calculator.calculate_road_access_horizon(
        road_status="BLOCKED",
        travel_time_minutes=45.0,
    )
    assert road_horizon == 0.0

    # In full SCH calculation:
    telemetry = {
        "road_status": "BLOCKED",
        "travel_time_minutes": 120.0,
        "drug_stocks": {"MED-ORS-20.5G": 100.0, "MED-ZINC-20MG": 100.0},
        "drug_demands_per_hour": {"MED-ORS-20.5G": 2.0, "MED-ZINC-20MG": 2.0},
        "nurse_on_duty": 3,
        "anm_on_duty": 3,
        "grid_available": True,
        "battery_charge_percent": 100.0,
        "generator_fuel_liters": 80.0,
    }

    assessment = sch_calculator.compute_sch(
        phc_id="PHC-TEST-001",
        service_id="diarrhoeal_care",
        telemetry=telemetry,
    )

    # Road access is 0.0, so overall SCH is 0.0 and status is CRITICAL
    assert assessment.sch_hours == 0.0
    assert assessment.status == "CRITICAL"
    assert assessment.limiting_dependency == "road_access"
    # Next limiting is drug
    assert "drug_" in assessment.next_limiting_dependency


def test_sch_status_thresholds(sch_calculator):
    """Verify:
    HEALTHY >= 72h
    WATCH = 48h to <72h
    CRITICAL < 48h
    """
    # 1. Healthy: all horizons >= 72h
    telemetry_healthy = {
        "road_status": "OPEN",
        "travel_time_minutes": 30.0,
        "drug_stocks": {"ORS": 500.0, "zinc": 500.0, "IV_fluids": 500.0},
        "drug_demands_per_hour": {"ORS": 2.0, "zinc": 2.0, "IV_fluids": 2.0},  # 250h
        "nurse_on_duty": 4,
        "anm_on_duty": 4,
        "shift_hours_remaining": 12.0,
        "absenteeism_rate": 0.0,
        "total_beds": 10,
        "occupied_beds": 2,
        "bed_admissions_per_hour": 0.05,  # (10-2)/0.05 = 160h
        "grid_available": True,
        "battery_charge_percent": 100.0,
        "generator_fuel_liters": 100.0,
    }
    result_healthy = sch_calculator.compute_sch("PHC-001", "diarrhoeal_care", telemetry_healthy)
    assert result_healthy.sch_hours >= 72.0
    assert result_healthy.status == "HEALTHY"

    # 2. Watch: 48h <= horizon < 72h
    # stock = 100, demand = 2/hr -> 50h
    telemetry_watch = dict(telemetry_healthy)
    telemetry_watch["drug_stocks"] = {"ORS": 100.0, "zinc": 500.0, "IV_fluids": 500.0}
    telemetry_watch["drug_demands_per_hour"] = {"ORS": 2.0, "zinc": 2.0, "IV_fluids": 2.0}
    result_watch = sch_calculator.compute_sch("PHC-001", "diarrhoeal_care", telemetry_watch)
    assert 48.0 <= result_watch.sch_hours < 72.0
    assert result_watch.status == "WATCH"
    assert "ORS" in result_watch.limiting_dependency

    # 3. Critical: horizon < 48h
    # stock = 40, demand = 2/hr -> 20h
    telemetry_critical = dict(telemetry_healthy)
    telemetry_critical["drug_stocks"] = {"ORS": 40.0, "zinc": 500.0, "IV_fluids": 500.0}
    telemetry_critical["drug_demands_per_hour"] = {"ORS": 2.0, "zinc": 2.0, "IV_fluids": 2.0}
    result_critical = sch_calculator.compute_sch("PHC-001", "diarrhoeal_care", telemetry_critical)
    assert result_critical.sch_hours < 48.0
    assert result_critical.status == "CRITICAL"
    assert "ORS" in result_critical.limiting_dependency


def test_maternal_delivery_bed_limiting_dependency(sch_calculator):
    """Test maternal delivery where bed occupancy reaches limit quickly."""
    telemetry = {
        "road_status": "OPEN",
        "travel_time_minutes": 30.0,
        "drug_stocks": {"MED-OXYTOCIN-10IU": 200.0, "MED-MISOPROSTOL-200MCG": 200.0},
        "drug_demands_per_hour": {"MED-OXYTOCIN-10IU": 1.0, "MED-MISOPROSTOL-200MCG": 1.0},
        "nurse_on_duty": 3,
        "anm_on_duty": 3,
        "total_beds": 10,
        "occupied_beds": 8,  # 2 beds left
        "bed_admissions_per_hour": 0.5,  # 2 / 0.5 = 4 hours horizon!
        "grid_available": True,
        "battery_charge_percent": 100.0,
        "generator_fuel_liters": 100.0,
    }
    assessment = sch_calculator.compute_sch("PHC-002", "maternal_delivery", telemetry)
    assert assessment.limiting_dependency == "beds"
    assert assessment.sch_hours == 4.0
    assert assessment.status == "CRITICAL"


def test_power_outage_depletion(sch_calculator):
    """Test power backup horizon when grid is down."""
    # battery 50% * 8h = 4h; fuel 22L / 2.2L/h = 10h -> total 14h
    horizon = sch_calculator.calculate_power_horizon(
        grid_available=False,
        battery_charge_percent=50.0,
        generator_fuel_liters=22.0,
        burn_rate_liters_per_hour=2.2,
        battery_discharge_hours=8.0,
    )
    assert horizon == 14.0
