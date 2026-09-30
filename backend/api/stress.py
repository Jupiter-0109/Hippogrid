"""Reverse Stress API Endpoints for HippoGrid.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Endpoints:
- GET /api/v1/stress/frontier: Returns minimal compound shock and Resilience Frontier points
  comparing unmitigated failure probability vs HippoGrid intervention.
- GET /api/v1/stress/fragility: Returns PHC fragility ranking and critical bottleneck service lines.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from backend.stress.reverse_stress import ReverseStressEngine

router = APIRouter(prefix="/api/v1/stress", tags=["reverse-stress"])

# Cached engine and precomputed report for sub-second query performance
STRESS_ENGINE = ReverseStressEngine(seed=42)
CACHED_REPORT = None


def get_or_create_report():
    global CACHED_REPORT
    if CACHED_REPORT is None:
        CACHED_REPORT = STRESS_ENGINE.generate_full_report()
    return CACHED_REPORT


@router.get("/frontier")
def get_resilience_frontier() -> Dict[str, Any]:
    """Retrieve reverse stress testing resilience frontier comparing unmitigated vs HippoGrid."""
    report = get_or_create_report()
    return {
        "status": "ok",
        "question": "What is the smallest plausible compound shock that causes at least 3 PHCs to lose an essential service for 48 continuous hours?",
        "minimal_compound_shock": report.minimal_compound_shock,
        "critical_phcs": report.critical_phcs,
        "critical_services": report.critical_services,
        "comparison_summary": report.comparison_summary,
        "frontier_data": report.frontier,
    }


@router.get("/fragility")
def get_fragility_ranking() -> Dict[str, Any]:
    """Retrieve network fragility ranking across all 36 PHCs."""
    report = get_or_create_report()
    return {
        "status": "ok",
        "total_phcs_analyzed": len(report.fragility_ranking),
        "critical_phcs": report.critical_phcs,
        "critical_services": report.critical_services,
        "ranking": report.fragility_ranking,
    }
