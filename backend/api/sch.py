"""Service Capability Horizon (SCH) API endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.repositories.network_repository import NetworkRepository
from backend.db.session import get_db
from backend.sch.horizon import ServiceCapabilityHorizonCalculator
from backend.sch.service_graph import ServiceCapabilityGraph

router = APIRouter(prefix="/api/v1", tags=["service-capability-horizon"])
calc = ServiceCapabilityHorizonCalculator()
graph = ServiceCapabilityGraph()


def _get_mock_or_db_telemetry(phc_code: str) -> Dict[str, Any]:
    """Retrieve current operational telemetry for a PHC."""
    # Deterministic representative telemetry based on PHC code
    is_remote = "05" in phc_code or "06" in phc_code
    return {
        "road_status": "DEGRADED" if is_remote else "OPEN",
        "travel_time_minutes": 75.0 if is_remote else 40.0,
        "grid_available": not is_remote,
        "battery_charge_percent": 85.0 if is_remote else 100.0,
        "generator_fuel_liters": 45.0 if is_remote else 90.0,
        "total_beds": 6,
        "occupied_beds": 4 if is_remote else 2,
        "bed_admissions_per_hour": 0.2,
        "nurse_on_duty": 2 if not is_remote else 1,
        "anm_on_duty": 2,
        "absenteeism_rate": 0.15 if is_remote else 0.05,
        "shift_hours_remaining": 8.0,
        "drug_stocks": {
            "ORS": 120.0,
            "zinc": 90.0,
            "IV_fluids": 25.0,
            "oxytocin": 20.0,
            "paracetamol": 150.0,
            "ACT_antimalarial": 40.0,
            "vaccine_penta": 30.0,
            "amlodipine": 110.0,
        },
        "drug_demands_per_hour": {
            "ORS": 2.0,
            "zinc": 1.2,
            "IV_fluids": 0.8,
            "oxytocin": 0.5,
            "paracetamol": 2.5,
            "ACT_antimalarial": 0.6,
            "vaccine_penta": 0.4,
            "amlodipine": 1.0,
        },
    }


@router.get("/sch")
def get_all_sch(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Return SCH assessments for all monitored PHCs across all 4 services."""
    repo = NetworkRepository(db)
    phcs = repo.list_phcs()
    phc_list = phcs if phcs else [{"code": f"PHC-DST-A1-{i:02d}", "id": str(i)} for i in range(1, 7)]

    results: List[Dict[str, Any]] = []
    for p in phc_list:
        p_code = p.code if hasattr(p, "code") else p["code"]
        p_id = str(p.id) if hasattr(p, "id") else p["id"]
        p_name = p.name if hasattr(p, "name") else p.get("name", p_code) if isinstance(p, dict) else p_code
        telemetry = _get_mock_or_db_telemetry(p_code)

        for svc in graph.list_services():
            assessment = calc.compute_sch(p_id, svc.id, telemetry)
            results.append(
                {
                    "phc_id": assessment.phc_id,
                    "phc_code": p_code,
                    "phc_name": p_name,
                    "service_id": svc.id,
                    "service": assessment.service,
                    "sch_hours": assessment.sch_hours,
                    "status": assessment.status,
                    "limiting_dependency": assessment.limiting_dependency,
                    "next_limiting_dependency": assessment.next_limiting_dependency,
                }
            )

    return results


@router.get("/sch/{phc_id}")
def get_phc_sch(phc_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Return SCH assessments for a specific PHC across all 4 services."""
    telemetry = _get_mock_or_db_telemetry(phc_id)
    results: List[Dict[str, Any]] = []

    for svc in graph.list_services():
        assessment = calc.compute_sch(phc_id, svc.id, telemetry)
        results.append(
            {
                "phc_id": assessment.phc_id,
                "service": assessment.service,
                "sch_hours": assessment.sch_hours,
                "status": assessment.status,
                "limiting_dependency": assessment.limiting_dependency,
                "next_limiting_dependency": assessment.next_limiting_dependency,
            }
        )

    return results
