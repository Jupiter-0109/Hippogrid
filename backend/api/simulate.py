"""Simulation API Router for HippoGrid Network Digital Twin.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Endpoints:
- POST /api/v1/simulate: Execute scenario or Monte Carlo simulation run.
- GET /api/v1/simulate/results: Retrieve latest simulation results or summary.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.sim.scenario import (
    MonteCarloResult,
    NetworkDigitalTwin,
    ScenarioParams,
    SimulationRunResult,
)

router = APIRouter(prefix="/api/v1/simulate", tags=["simulation"])

# In-memory storage for latest simulation outputs
LATEST_SIMULATION_RESULT: Optional[Dict[str, Any]] = None
TWIN_ENGINE = NetworkDigitalTwin(seed=42)


class SimulateRequest(BaseModel):
    name: Optional[str] = "Monsoon Stress Scenario"
    rain_multiplier: float = Field(1.0, ge=0.5, le=5.0)
    road_closure_fraction: float = Field(0.0, ge=0.0, le=1.0)
    staff_absence_fraction: float = Field(0.0, ge=0.0, le=0.8)
    demand_surge_multiplier: float = Field(1.0, ge=0.5, le=4.0)
    start_date: str = "2025-06-01"
    duration_days: int = Field(7, ge=1, le=30)
    run_monte_carlo: bool = False
    monte_carlo_iterations: int = Field(50, ge=10, le=200)


@router.post("")
def run_simulation_endpoint(req: SimulateRequest) -> Dict[str, Any]:
    """Execute scenario simulation run with coupled inventory, staff, roads, and patient spillover."""
    global LATEST_SIMULATION_RESULT

    scenario = ScenarioParams(
        name=req.name or "Scenario Run",
        rain_multiplier=req.rain_multiplier,
        road_closure_fraction=req.road_closure_fraction,
        staff_absence_fraction=req.staff_absence_fraction,
        demand_surge_multiplier=req.demand_surge_multiplier,
        start_date=req.start_date,
        duration_days=req.duration_days,
    )

    if req.run_monte_carlo:
        mc_result = TWIN_ENGINE.run_monte_carlo(
            scenario=scenario,
            n_simulations=req.monte_carlo_iterations,
        )

        response_data = {
            "mode": "MONTE_CARLO",
            "scenario": {
                "name": scenario.name,
                "rain_multiplier": scenario.rain_multiplier,
                "road_closure_fraction": scenario.road_closure_fraction,
                "staff_absence_fraction": scenario.staff_absence_fraction,
                "demand_surge_multiplier": scenario.demand_surge_multiplier,
                "duration_days": scenario.duration_days,
            },
            "n_simulations": mc_result.n_simulations,
            "mean_network_served_ratio": mc_result.mean_network_served_ratio,
            "conservation_verified": mc_result.conservation_verified,
            "failure_probabilities": [
                {
                    "phc_code": p.phc_code,
                    "service_id": p.service_id,
                    "failure_probability": p.failure_probability,
                    "mean_unserved_patients": p.mean_unserved_patients,
                    "risk_level": p.risk_level,
                }
                for p in mc_result.service_failure_probabilities
            ],
        }
    else:
        single_res = TWIN_ENGINE.run_simulation(scenario)
        response_data = {
            "mode": "SINGLE_TRAJECTORY",
            "scenario": {
                "name": scenario.name,
                "rain_multiplier": scenario.rain_multiplier,
                "road_closure_fraction": scenario.road_closure_fraction,
                "staff_absence_fraction": scenario.staff_absence_fraction,
                "demand_surge_multiplier": scenario.demand_surge_multiplier,
                "duration_days": scenario.duration_days,
            },
            "total_initial_demand": single_res.total_initial_demand,
            "total_served": single_res.total_served,
            "total_unserved": single_res.total_unserved,
            "total_spillover_events": single_res.total_spillover_events,
            "conservation_verified": abs(
                single_res.total_initial_demand - (single_res.total_served + single_res.total_unserved)
            ) < 0.5,
            "daily_summary": [
                {
                    "date": r.date,
                    "phc_code": r.phc_code,
                    "service_id": r.service_id,
                    "initial_demand": r.initial_demand,
                    "spillover_in": r.spillover_in,
                    "effective_demand": r.effective_demand,
                    "served_demand": r.served_demand,
                    "unserved_demand": r.unserved_demand,
                    "is_failed": r.is_failed,
                    "limiting_dependency": r.limiting_dependency,
                    "sch_hours": r.sch_hours,
                }
                for r in single_res.daily_records[:100]  # truncate payload for responsiveness
            ],
        }

    LATEST_SIMULATION_RESULT = response_data
    return response_data


@router.get("/results")
def get_simulation_results() -> Dict[str, Any]:
    """Retrieve the latest network digital twin simulation results."""
    global LATEST_SIMULATION_RESULT
    if LATEST_SIMULATION_RESULT is None:
        # Run a default baseline run
        baseline = ScenarioParams(name="Zero-Shock Baseline")
        res = TWIN_ENGINE.run_simulation(baseline)
        LATEST_SIMULATION_RESULT = {
            "mode": "SINGLE_TRAJECTORY",
            "scenario": {
                "name": baseline.name,
                "rain_multiplier": 1.0,
                "road_closure_fraction": 0.0,
                "staff_absence_fraction": 0.0,
                "demand_surge_multiplier": 1.0,
                "duration_days": 7,
            },
            "total_initial_demand": res.total_initial_demand,
            "total_served": res.total_served,
            "total_unserved": res.total_unserved,
            "conservation_verified": True,
            "message": "Initialized with zero-shock baseline run",
        }

    return LATEST_SIMULATION_RESULT
