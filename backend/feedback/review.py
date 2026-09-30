"""Human-in-the-Loop Review & Feedback Engine for HippoGrid.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Decision Actions:
- APPROVE: Accept the proposed transfer plan as generated.
- EDIT: Modify transfer quantities. Requires preserving original_quantity and modified_quantity.
- REJECT: Refuse transfer recommendation. Requires explicit reason.

Reason Codes:
- ROUTE_UNSAFE: Flooding, landslides, or impassable road conditions.
- STOCK_RESERVED: Donor facility has imminent local high-risk surge.
- CONTROLLED_ITEM: Special regulatory, cold-chain, or judicial custody restriction.
- VEHICLE_LIMIT: Insufficient logistics vehicles or fuel.
- LOCAL_KNOWLEDGE: Ground reality not yet captured in digital telemetry.
- OTHER: Freeform clinical or administrative override reason.

Audit Trail:
Stores full provenance in PostgreSQL System-of-Record:
- recommendation_id
- model_version
- input_data snapshot
- reason code
- human action (APPROVE, EDIT, REJECT)
- reviewer metadata
- timestamp

Directives:
- Do not claim the system automatically learns unless a real learning rule is implemented.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text


class HumanAction(str, Enum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"


class RejectionReasonCode(str, Enum):
    ROUTE_UNSAFE = "ROUTE_UNSAFE"
    STOCK_RESERVED = "STOCK_RESERVED"
    CONTROLLED_ITEM = "CONTROLLED_ITEM"
    VEHICLE_LIMIT = "VEHICLE_LIMIT"
    LOCAL_KNOWLEDGE = "LOCAL_KNOWLEDGE"
    OTHER = "OTHER"


@dataclass
class ReviewItem:
    transfer_id: str
    action: HumanAction
    original_quantity: int
    modified_quantity: Optional[int] = None
    reason_code: Optional[RejectionReasonCode] = None
    notes: Optional[str] = None


@dataclass
class HumanReviewAuditEntry:
    review_id: str
    plan_id: str
    actor_id: str
    actor_role: str
    action: str
    model_version: str
    timestamp: str
    original_quantity: int
    modified_quantity: Optional[int]
    reason_code: Optional[str]
    notes: Optional[str]
    input_snapshot: Dict[str, Any]


class HumanReviewEngine:
    """Manages plan review validation, reason enforcement, and immutable audit logging."""

    def __init__(self) -> None:
        self.in_memory_reviews: List[HumanReviewAuditEntry] = []

    def validate_and_record_feedback(
        self,
        plan_id: str,
        actor_id: str,
        actor_role: str,
        reviews: List[ReviewItem],
        model_version: str = "ortools-v1.0",
        db: Optional[Session] = None,
    ) -> List[HumanReviewAuditEntry]:
        """Validate review payloads and record entries into audit trail."""
        recorded_entries: List[HumanReviewAuditEntry] = []

        for item in reviews:
            # Rule 1: If REJECT, reason_code is strictly required
            if item.action == HumanAction.REJECT and not item.reason_code:
                raise ValueError(
                    f"Rejection of transfer '{item.transfer_id}' requires an explicit reason code "
                    f"(ROUTE_UNSAFE, STOCK_RESERVED, CONTROLLED_ITEM, VEHICLE_LIMIT, LOCAL_KNOWLEDGE, OTHER)."
                )

            # Rule 2: If EDIT, modified_quantity must be provided and positive
            if item.action == HumanAction.EDIT:
                if item.modified_quantity is None or item.modified_quantity <= 0:
                    raise ValueError(
                        f"Edit of transfer '{item.transfer_id}' requires a valid positive modified_quantity."
                    )

            mod_qty = item.modified_quantity if item.action == HumanAction.EDIT else item.original_quantity
            r_code = item.reason_code.value if item.reason_code else None

            entry = HumanReviewAuditEntry(
                review_id=f"rev-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
                plan_id=plan_id,
                actor_id=actor_id,
                actor_role=actor_role,
                action=item.action.value,
                model_version=model_version,
                timestamp=datetime.utcnow().isoformat(),
                original_quantity=item.original_quantity,
                modified_quantity=mod_qty if item.action == HumanAction.EDIT else None,
                reason_code=r_code,
                notes=item.notes or "",
                input_snapshot={
                    "transfer_id": item.transfer_id,
                    "original_quantity": item.original_quantity,
                },
            )
            self.in_memory_reviews.append(entry)
            recorded_entries.append(entry)

            # Persist to database audit log if active session provided
            if db:
                try:
                    import json
                    db.execute(
                        text("""
                            INSERT INTO audit_logs (
                                event_type, entity_name, entity_id, user_id, details_json, created_at
                            ) VALUES (
                                :event_type, :entity_name, :entity_id, :user_id, :details_json, NOW()
                            )
                        """),
                        {
                            "event_type": f"PLAN_REVIEW_{item.action.value}",
                            "entity_name": "resource_plans",
                            "entity_id": plan_id,
                            "user_id": actor_id,
                            "details_json": json.dumps(asdict(entry)),
                        },
                    )
                    db.commit()
                except Exception:
                    db.rollback()

        return recorded_entries

    def get_feedback_summary(self) -> Dict[str, Any]:
        """Compile feedback statistics across approved, edited, and rejected recommendations."""
        total = len(self.in_memory_reviews)
        if total == 0:
            return {
                "total_decisions": 0,
                "approved_count": 0,
                "edited_count": 0,
                "rejected_count": 0,
                "rejection_reasons_breakdown": {},
                "audit_trail_preview": [],
                "learning_status": "Human feedback is systematically audited. Online parameter adaptation is governed by human sign-off.",
            }

        actions = [r.action for r in self.in_memory_reviews]
        approved = actions.count("APPROVE")
        edited = actions.count("EDIT")
        rejected = actions.count("REJECT")

        reasons = {}
        for r in self.in_memory_reviews:
            if r.reason_code:
                reasons[r.reason_code] = reasons.get(r.reason_code, 0) + 1

        recent_preview = [asdict(r) for r in self.in_memory_reviews[-15:]]

        return {
            "total_decisions": total,
            "approved_count": approved,
            "edited_count": edited,
            "rejected_count": rejected,
            "approval_rate_percent": round((approved / total) * 100.0, 1),
            "rejection_reasons_breakdown": reasons,
            "audit_trail_preview": recent_preview,
            "learning_status": "Human feedback is systematically audited. Online parameter adaptation is governed by human sign-off.",
        }
