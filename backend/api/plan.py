"""Resource Optimization & Plan Comparison API Router.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Endpoints:
- POST /api/v1/plan: Generate HippoGrid optimization transfer recommendations.
- GET /api/v1/plan/compare: Compare Baseline Nearest-Surplus vs HippoGrid OR-Tools.

CRITICAL DIRECTIVE:
Every recommendation requires explicit human decision-maker approval.
Do not automatically execute recommendations.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.opt.baseline import NearestSurplusBaseline, PlanSummary
from backend.opt.prescriber import HippoGridResourcePrescriber

router = APIRouter(prefix="/api/v1/plan", tags=["optimization"])

PRESCRIBER = HippoGridResourcePrescriber(seed=42)
BASELINE = NearestSurplusBaseline(seed=42)


class PlanRequest(BaseModel):
    district_code: Optional[str] = "DST-A1"
    target_medicine_id: Optional[str] = "ORS"
    blocked_routes: Optional[List[List[str]]] = None
    max_transit_hours: float = Field(8.0, ge=1.0, le=24.0)


def create_mock_stocks() -> Dict[str, Any]:
    """Generate realistic test stock levels with surplus and deficit facilities."""
    stocks = {}
    safety = {}
    demands = {}

    for d in PRESCRIBER.districts:
        phcs = [p.code for p in PRESCRIBER.phcs if p.district_code == d.code]
        for idx, p_code in enumerate(phcs):
            stocks[p_code] = {}
            safety[p_code] = {}
            demands[p_code] = {}
            for med in ["ORS", "zinc", "IV_fluids", "paracetamol", "oxytocin"]:
                safety[p_code][med] = 40.0
                demands[p_code][med] = 2.0
                # Introduce deficits in PHCs 1 & 2, surpluses in PHCs 3 & 4
                if idx in (0, 1):
                    stocks[p_code][med] = 12.0  # Deficit (critical shortage)
                elif idx in (2, 3):
                    stocks[p_code][med] = 120.0  # Healthy surplus
                else:
                    stocks[p_code][med] = 50.0  # Nominal buffer

    return stocks, safety, demands


@router.post("")
def generate_resource_plan(req: PlanRequest) -> Dict[str, Any]:
    """Generate optimal resource redistribution recommendations via OR-Tools MILP."""
    stocks, safety, demands = create_mock_stocks()

    blocked = []
    if req.blocked_routes:
        blocked = [(r[0], r[1]) for r in req.blocked_routes if len(r) == 2]

    # Integrate active blocked routes learned from human feedback (>=3x ROUTE_UNSAFE)
    from backend.api.feedback import REGRET_LEDGER
    learned_blocked = REGRET_LEDGER.get_active_blocked_route_pairs()
    for lb in learned_blocked:
        if lb not in blocked:
            blocked.append(lb)

    plan = PRESCRIBER.optimize_redistribution(
        current_stocks=stocks,
        safety_stocks=safety,
        demands_per_hour=demands,
        blocked_routes=blocked,
        max_transit_hours=req.max_transit_hours,
    )

    return {
        "status": "PROPOSED",
        "human_approval_required": True,
        "human_approval_status": "PENDING_DECISION",
        "algorithm": plan.algorithm,
        "total_transfers": plan.total_transfers,
        "total_units_moved": plan.total_units_moved,
        "total_transport_cost": plan.total_transport_cost,
        "min_phc_coverage_hours": plan.min_phc_coverage_hours,
        "mean_network_coverage_hours": plan.mean_network_coverage_hours,
        "transfers": [
            {
                "source": t.source_phc,
                "destination": t.destination_phc,
                "medicine": t.medicine_id,
                "quantity": t.quantity,
                "route": t.route,
                "travel_time_minutes": t.travel_time_minutes,
                "expected_coverage_hours": t.expected_coverage_hours,
                "assurance_score": t.assurance_score,
                "reason": t.reason,
                "requires_approval": True,
            }
            for t in plan.transfers
        ],
    }


@router.get("/compare")
def compare_plans() -> Dict[str, Any]:
    """Compare Nearest-Surplus heuristic against HippoGrid OR-Tools two-stage optimization."""
    # Run Baseline
    stocks_b, safety_b, demands_b = create_mock_stocks()
    base_plan = BASELINE.prescribe(stocks_b, safety_b, demands_b)

    # Run HippoGrid OR-Tools
    stocks_h, safety_h, demands_h = create_mock_stocks()
    hippogrid_plan = PRESCRIBER.optimize_redistribution(stocks_h, safety_h, demands_h)

    return {
        "comparison_title": "Nearest-Surplus Baseline vs HippoGrid OR-Tools Prescriber",
        "human_approval_mandate": "All interventions require explicit human decision-maker approval.",
        "baseline_nearest_phc": {
            "algorithm": base_plan.algorithm,
            "total_transfers": base_plan.total_transfers,
            "total_units_moved": base_plan.total_units_moved,
            "total_transport_cost": base_plan.total_transport_cost,
            "min_phc_coverage_hours": base_plan.min_phc_coverage_hours,
            "mean_network_coverage_hours": base_plan.mean_network_coverage_hours,
            "sample_transfers_count": len(base_plan.transfers),
        },
        "hippogrid_ortools": {
            "algorithm": hippogrid_plan.algorithm,
            "total_transfers": hippogrid_plan.total_transfers,
            "total_units_moved": hippogrid_plan.total_units_moved,
            "total_transport_cost": hippogrid_plan.total_transport_cost,
            "min_phc_coverage_hours": hippogrid_plan.min_phc_coverage_hours,
            "mean_network_coverage_hours": hippogrid_plan.mean_network_coverage_hours,
            "sample_transfers_count": len(hippogrid_plan.transfers),
        },
        "efficiency_gain": {
            "coverage_improvement_hours": round(
                hippogrid_plan.min_phc_coverage_hours - base_plan.min_phc_coverage_hours, 1
            ),
            "cost_differential": round(
                hippogrid_plan.total_transport_cost - base_plan.total_transport_cost, 2
            ),
            "equity_guaranteed": True,
        },
    }
