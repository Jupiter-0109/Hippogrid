"""Feedback API Router for HippoGrid Human-in-the-Loop Review & Regret Ledger.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Endpoints:
- POST /api/v1/feedback: Submit review decision (APPROVE, EDIT, REJECT with reason code).
- GET /api/v1/feedback/summary: Retrieve feedback distribution and audit trail.
- GET /api/v1/feedback/regret-ledger: Retrieve human overrides and operational constraint learning ledger.
- GET /api/v1/feedback/blocked-routes: Retrieve actively blocked routes identified by repeated human overrides.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.feedback.review import (
    HumanAction,
    HumanReviewEngine,
    RejectionReasonCode,
    ReviewItem,
)
from backend.feedback.regret_ledger import RegretLedgerEngine

router = APIRouter(prefix="/api/v1/feedback", tags=["human-review"])

REVIEW_ENGINE = HumanReviewEngine()
REGRET_LEDGER = RegretLedgerEngine(block_threshold=3, block_duration_hours=72)


class ReviewSubmissionItem(BaseModel):
    transfer_id: str
    action: HumanAction
    original_quantity: int = Field(..., ge=1)
    modified_quantity: Optional[int] = Field(None, ge=1)
    reason_code: Optional[RejectionReasonCode] = None
    notes: Optional[str] = None
    source_phc: Optional[str] = "PHC-DST-A1-03"
    destination_phc: Optional[str] = "PHC-DST-A1-04"
    medicine: Optional[str] = "ORS"


class FeedbackSubmitRequest(BaseModel):
    plan_id: str
    actor_id: str = "dr_rajesh_cmo"
    actor_role: str = "Chief Medical Officer"
    model_version: Optional[str] = "ortools-v1.0"
    reviews: List[ReviewSubmissionItem]


@router.post("")
def submit_plan_feedback(
    req: FeedbackSubmitRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Submit human review decision for proposed resource reallocation plan."""
    review_items = [
        ReviewItem(
            transfer_id=item.transfer_id,
            action=item.action,
            original_quantity=item.original_quantity,
            modified_quantity=item.modified_quantity,
            reason_code=item.reason_code,
            notes=item.notes,
        )
        for item in req.reviews
    ]

    try:
        recorded = REVIEW_ENGINE.validate_and_record_feedback(
            plan_id=req.plan_id,
            actor_id=req.actor_id,
            actor_role=req.actor_role,
            reviews=review_items,
            model_version=req.model_version or "ortools-v1.0",
            db=db,
        )

        # Feed into Regret Ledger for human-in-the-loop operational constraint learning
        for item in req.reviews:
            REGRET_LEDGER.record_decision(
                plan_id=req.plan_id,
                transfer_id=item.transfer_id,
                source_phc=item.source_phc or "PHC-DST-A1-03",
                destination_phc=item.destination_phc or "PHC-DST-A1-04",
                medicine=item.medicine or "ORS",
                original_quantity=item.original_quantity,
                human_decision=item.action.value,
                reason_code=item.reason_code.value if item.reason_code else None,
                modified_quantity=item.modified_quantity,
                notes=item.notes,
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "RECORDED",
        "plan_id": req.plan_id,
        "recorded_decisions_count": len(recorded),
        "audit_entries": [
            {
                "review_id": r.review_id,
                "action": r.action,
                "original_quantity": r.original_quantity,
                "modified_quantity": r.modified_quantity,
                "reason_code": r.reason_code,
                "timestamp": r.timestamp,
            }
            for r in recorded
        ],
        "blocked_routes_active_count": len(REGRET_LEDGER.get_active_blocked_route_pairs()),
        "message": "Human decision recorded in immutable audit log and Regret Ledger.",
    }


@router.get("/summary")
def get_feedback_summary() -> Dict[str, Any]:
    """Retrieve feedback breakdown statistics and audit trail."""
    return REVIEW_ENGINE.get_feedback_summary()


@router.get("/regret-ledger")
def get_regret_ledger() -> Dict[str, Any]:
    """Retrieve Human-in-the-Loop Regret Ledger showing AI recommendations, Human overrides, Reasons, and Outcomes."""
    return REGRET_LEDGER.get_ledger_summary()


@router.get("/blocked-routes")
def get_blocked_routes() -> Dict[str, Any]:
    """Retrieve currently active blocked routes identified by repeated (>=3x) ROUTE_UNSAFE rejections."""
    blocked = REGRET_LEDGER.get_blocked_routes()
    return {
        "policy": "Route marked temporarily blocked after >=3x ROUTE_UNSAFE rejections with 72h expiry.",
        "active_blocked_routes": [
            {
                "route_key": b.route_key,
                "source_phc": b.source_phc,
                "destination_phc": b.destination_phc,
                "rejection_count": b.rejection_count,
                "reason": b.reason,
                "blocked_at": b.blocked_at,
                "expires_at": b.expires_at,
                "active": b.active,
            }
            for b in blocked
            if b.active
        ],
        "expired_blocked_routes": [
            {
                "route_key": b.route_key,
                "rejection_count": b.rejection_count,
                "expired_at": b.expires_at,
            }
            for b in blocked
            if not b.active
        ],
    }
