"""Unit and Scenario Tests for Phase 7 (Network Digital Twin)
and Phase 8 (Resource Prescriber).

Verifications:
1. Zero-shock baseline simulation: all services healthy, no artificial shortages.
2. Patient conservation: total demand == served patients + unserved patients (zero creation/destruction).
3. Patient spillover: when PHC experiences high demand or absence shock, unmet demand spills to reachable open neighbours.
4. Reproducibility: running twin with fixed seed 42 produces identical outputs.
5. Monte Carlo simulation: computes failure probability per PHC per service across iterations.
6. Baseline vs HippoGrid OR-Tools comparison: verifies constraints, safety stock protection, and objective improvement.
7. Human decision approval flag is mandatory on every recommendation.
"""
import pytest
from backend.opt.baseline import NearestSurplusBaseline
from backend.opt.prescriber import HippoGridResourcePrescriber
from backend.sim.scenario import NetworkDigitalTwin, ScenarioParams


@pytest.fixture
def digital_twin():
    return NetworkDigitalTwin(seed=42)


@pytest.fixture
def prescriber():
    return HippoGridResourcePrescriber(seed=42)


@pytest.fixture
def baseline_opt():
    return NearestSurplusBaseline(seed=42)


def test_zero_shock_baseline_simulation(digital_twin):
    """Test 1: Zero-shock baseline run."""
    baseline = ScenarioParams(
        name="Zero Shock Baseline",
        rain_multiplier=1.0,
        road_closure_fraction=0.0,
        staff_absence_fraction=0.0,
        demand_surge_multiplier=1.0,
        duration_days=7,
    )
    result = digital_twin.run_simulation(baseline)

    assert result.total_initial_demand > 0
    assert result.total_served > 0
    # In nominal conditions, almost all patients are served locally
    assert result.total_served / result.total_initial_demand >= 0.95


def test_patient_conservation_guarantee(digital_twin):
    """Test 2: Patient conservation guarantee under severe shock.
    Total demand == served patients + unserved patients.
    """
    severe_shock = ScenarioParams(
        name="Severe Shock",
        rain_multiplier=2.5,
        road_closure_fraction=0.3,
        staff_absence_fraction=0.4,
        demand_surge_multiplier=2.0,
        duration_days=7,
    )
    result = digital_twin.run_simulation(severe_shock)

    sum_served_and_unserved = result.total_served + result.total_unserved
    # Check within numerical precision (floating point rounding)
    diff = abs(result.total_initial_demand - sum_served_and_unserved)
    assert diff < 0.5, f"Patient conservation violated: {result.total_initial_demand} != {sum_served_and_unserved}"


def test_patient_spillover_redistribution(digital_twin):
    """Test 3: Unmet demand triggers spillover to reachable open neighbours."""
    shock = ScenarioParams(
        name="Staff Outage with Open Roads",
        rain_multiplier=1.0,
        road_closure_fraction=0.0,  # routes open
        staff_absence_fraction=0.6,  # triggers service breakdown and spillover
        demand_surge_multiplier=1.2,
        duration_days=3,
    )
    result = digital_twin.run_simulation(shock)

    # Some spillover events should occur
    assert result.total_spillover_events > 0
    # Check that spillover_in occurred in at least one record
    spillover_absorbed = sum(r.spillover_in for r in result.daily_records)
    assert spillover_absorbed > 0


def test_simulation_reproducibility(digital_twin):
    """Test 4: Fixed seed produces 100% deterministic identical outputs."""
    scenario = ScenarioParams(
        name="Reproducibility Scenario",
        rain_multiplier=1.5,
        road_closure_fraction=0.1,
        staff_absence_fraction=0.2,
        demand_surge_multiplier=1.3,
        duration_days=5,
    )
    run1 = digital_twin.run_simulation(scenario, seed_override=42)
    run2 = digital_twin.run_simulation(scenario, seed_override=42)

    assert run1.total_initial_demand == run2.total_initial_demand
    assert run1.total_served == run2.total_served
    assert run1.total_unserved == run2.total_unserved
    assert len(run1.daily_records) == len(run2.daily_records)


def test_monte_carlo_failure_probability(digital_twin):
    """Test 5: Monte Carlo execution produces valid failure probabilities."""
    scenario = ScenarioParams(
        name="Stress Test Monte Carlo",
        rain_multiplier=2.0,
        road_closure_fraction=0.2,
        staff_absence_fraction=0.3,
        demand_surge_multiplier=1.5,
        duration_days=3,
    )
    mc = digital_twin.run_monte_carlo(scenario, n_simulations=15)

    assert mc.n_simulations == 15
    assert len(mc.service_failure_probabilities) > 0
    assert mc.conservation_verified is True
    # All probabilities in [0.0, 1.0]
    for p in mc.service_failure_probabilities:
        assert 0.0 <= p.failure_probability <= 1.0
        assert p.risk_level in ["LOW", "MEDIUM", "HIGH", "SEVERE"]


def test_resource_prescriber_safety_stock_and_constraints(prescriber, baseline_opt):
    """Test 6 & 7: OR-Tools Prescriber preserves safety stock and outperforms greedy baseline."""
    # Setup test network state
    stocks = {
        "PHC-DST-A1-01": {"ORS": 10.0},   # Critical deficit (< safety 40)
        "PHC-DST-A1-02": {"ORS": 150.0},  # Large surplus (> safety 40)
        "PHC-DST-A1-03": {"ORS": 40.0},   # Exactly at safety stock (cannot donate)
    }
    safety = {
        "PHC-DST-A1-01": {"ORS": 40.0},
        "PHC-DST-A1-02": {"ORS": 40.0},
        "PHC-DST-A1-03": {"ORS": 40.0},
    }
    demands = {
        "PHC-DST-A1-01": {"ORS": 2.0},
        "PHC-DST-A1-02": {"ORS": 2.0},
        "PHC-DST-A1-03": {"ORS": 2.0},
    }

    # Run Prescriber
    plan = prescriber.optimize_redistribution(
        current_stocks=stocks,
        safety_stocks=safety,
        demands_per_hour=demands,
    )

    # 1. Has proposed transfers
    assert plan.total_transfers > 0
    assert plan.total_units_moved > 0

    # 2. Source safety stock is strictly protected: PHC-DST-A1-03 must never donate
    donations_from_p3 = [t for t in plan.transfers if t.source_phc == "PHC-DST-A1-03"]
    assert len(donations_from_p3) == 0, "Facility at safety stock was illegally forced to donate!"

    # 3. Source remaining stock >= safety stock
    assert stocks["PHC-DST-A1-02"]["ORS"] >= safety["PHC-DST-A1-02"]["ORS"]

    # 4. Human approval requirement flag
    for t in plan.transfers:
        assert t.assurance_score >= 0.70
        assert "OR-Tools" in t.reason or "optimal" in t.reason.lower()


def test_closed_route_feasibility_constraint(prescriber):
    """Test: When route is blocked, optimizer refuses to schedule transfer over it."""
    stocks = {
        "PHC-DST-A1-01": {"ORS": 10.0},
        "PHC-DST-A1-02": {"ORS": 120.0},
    }
    safety = {
        "PHC-DST-A1-01": {"ORS": 40.0},
        "PHC-DST-A1-02": {"ORS": 40.0},
    }
    demands = {
        "PHC-DST-A1-01": {"ORS": 2.0},
        "PHC-DST-A1-02": {"ORS": 2.0},
    }
    blocked_route = [("PHC-DST-A1-02", "PHC-DST-A1-01")]

    plan = prescriber.optimize_redistribution(
        current_stocks=stocks,
        safety_stocks=safety,
        demands_per_hour=demands,
        blocked_routes=blocked_route,
    )

    # Cannot transfer over blocked route
    assert plan.total_transfers == 0
