"""HippoGrid Regret Ledger & Human-in-the-Loop Constraint Engine.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Phase 14 Requirements:
- Use human decisions to identify repeated operational constraints.
- Track:
  - plan
  - original recommendation (AI recommendation)
  - human decision (Human override)
  - reason
  - outcome
- Policy Rule:
  If the same route is rejected with 'ROUTE_UNSAFE' 3 or more times:
  mark the route as temporarily blocked with an expiry date.
- Explicit Directive:
  Do not claim machine learning unless a real model is trained.
  This is a verifiable human-in-the-loop operational learning engine.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RegretLedgerEntry:
    entry_id: str
    plan_id: str
    transfer_id: str
    source_phc: str
    destination_phc: str
    route_key: str  # e.g., "PHC-DST-A1-03->PHC-DST-A1-04"
    medicine: str
    original_quantity: int
    ai_recommendation: Dict[str, Any]
    human_decision: str  # "APPROVE", "EDIT", "REJECT"
    human_override: Dict[str, Any]
    reason_code: Optional[str]
    notes: Optional[str]
    outcome: str
    timestamp: str


@dataclass
class BlockedRouteRecord:
    route_key: str
    source_phc: str
    destination_phc: str
    rejection_count: int
    reason: str
    blocked_at: str
    expires_at: str
    active: bool


class RegretLedgerEngine:
    """Tracks human overrides and dynamically synthesizes operational constraints."""

    def __init__(self, block_threshold: int = 3, block_duration_hours: int = 72) -> None:
        self.block_threshold = block_threshold
        self.block_duration_hours = block_duration_hours
        self.ledger: List[RegretLedgerEntry] = []
        self._seed_initial_history()

    def _seed_initial_history(self) -> None:
        """Seed realistic historical human decision events to demonstrate operational constraint learning."""
        now = datetime.utcnow()
        # Seed 3 ROUTE_UNSAFE rejections on route PHC-DST-A1-04 -> PHC-DST-A1-05 (Flash flood river bridge)
        r_key = "PHC-DST-A1-04->PHC-DST-A1-05"
        for i in range(3):
            t_time = (now - timedelta(hours=36 - i * 10)).isoformat()
            self.ledger.append(
                RegretLedgerEntry(
                    entry_id=f"rgt-init-00{i+1}",
                    plan_id=f"plan-hist-10{i+1}",
                    transfer_id=f"tr-hist-00{i+1}",
                    source_phc="PHC-DST-A1-04",
                    destination_phc="PHC-DST-A1-05",
                    route_key=r_key,
                    medicine="ORS",
                    original_quantity=40,
                    ai_recommendation={
                        "source": "PHC-DST-A1-04",
                        "destination": "PHC-DST-A1-05",
                        "quantity": 40,
                        "algorithm": "OR-Tools MILP",
                        "route": "Secondary Bridge Corridor SH-14",
                    },
                    human_decision="REJECT",
                    human_override={
                        "action": "REJECT",
                        "actor_role": "District Logistics Officer",
                    },
                    reason_code="ROUTE_UNSAFE",
                    notes="River submerged bridge approach under flash flood conditions.",
                    outcome="CORRIDOR_SUSPENDED_GROUND_ALERT",
                    timestamp=t_time,
                )
            )

        # Seed an EDIT override: CMO modified quantity due to local ICU reservation
        self.ledger.append(
            RegretLedgerEntry(
                entry_id="rgt-init-004",
                plan_id="plan-hist-104",
                transfer_id="tr-hist-004",
                source_phc="PHC-DST-A1-02",
                destination_phc="PHC-DST-A1-06",
                route_key="PHC-DST-A1-02->PHC-DST-A1-06",
                medicine="oxytocin",
                original_quantity=30,
                ai_recommendation={
                    "source": "PHC-DST-A1-02",
                    "destination": "PHC-DST-A1-06",
                    "quantity": 30,
                    "algorithm": "OR-Tools MILP",
                },
                human_decision="EDIT",
                human_override={
                    "action": "EDIT",
                    "original_quantity": 30,
                    "modified_quantity": 18,
                    "actor_role": "Chief Medical Officer",
                },
                reason_code="STOCK_RESERVED",
                notes="Reserved 12 ampoules for scheduled high-risk deliveries.",
                outcome="MODIFIED_DISPATCH_CONFIRMED",
                timestamp=(now - timedelta(hours=14)).isoformat(),
            )
        )

    def record_decision(
        self,
        plan_id: str,
        transfer_id: str,
        source_phc: str,
        destination_phc: str,
        medicine: str,
        original_quantity: int,
        human_decision: str,
        reason_code: Optional[str] = None,
        modified_quantity: Optional[int] = None,
        notes: Optional[str] = None,
        ai_recommendation: Optional[Dict[str, Any]] = None,
    ) -> RegretLedgerEntry:
        """Record human review event into Regret Ledger and assess operational constraints."""
        route_key = f"{source_phc}->{destination_phc}"
        entry_id = f"rgt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{transfer_id[:6]}"
        now = datetime.utcnow()

        outcome = "STANDARD_EXECUTION"
        if human_decision == "REJECT":
            if reason_code == "ROUTE_UNSAFE":
                outcome = "SAFETY_OVERRIDE_RECORDED"
            else:
                outcome = f"POLICY_REJECT_{reason_code or 'UNKNOWN'}"
        elif human_decision == "EDIT":
            outcome = f"PARAMETRIC_OVERRIDE_TO_{modified_quantity}"

        entry = RegretLedgerEntry(
            entry_id=entry_id,
            plan_id=plan_id,
            transfer_id=transfer_id,
            source_phc=source_phc,
            destination_phc=destination_phc,
            route_key=route_key,
            medicine=medicine,
            original_quantity=original_quantity,
            ai_recommendation=ai_recommendation or {
                "source": source_phc,
                "destination": destination_phc,
                "quantity": original_quantity,
                "medicine": medicine,
            },
            human_decision=human_decision,
            human_override={
                "action": human_decision,
                "modified_quantity": modified_quantity,
                "reason_code": reason_code,
            },
            reason_code=reason_code,
            notes=notes,
            outcome=outcome,
            timestamp=now.isoformat(),
        )

        self.ledger.append(entry)
        return entry

    def get_blocked_routes(self) -> List[BlockedRouteRecord]:
        """Identify routes rejected with ROUTE_UNSAFE 3 or more times.
        Marks them as temporarily blocked with an explicit expiry date.
        """
        route_unsafe_counts: Dict[str, List[RegretLedgerEntry]] = {}

        for entry in self.ledger:
            if entry.human_decision == "REJECT" and entry.reason_code == "ROUTE_UNSAFE":
                route_unsafe_counts.setdefault(entry.route_key, []).append(entry)

        blocked_records: List[BlockedRouteRecord] = []
        now = datetime.utcnow()

        for route_key, entries in route_unsafe_counts.items():
            if len(entries) >= self.block_threshold:
                # Latest rejection timestamp
                latest_ts = max(datetime.fromisoformat(e.timestamp) for e in entries)
                expires_at = latest_ts + timedelta(hours=self.block_duration_hours)
                is_active = now < expires_at

                src, dst = route_key.split("->")
                blocked_records.append(
                    BlockedRouteRecord(
                        route_key=route_key,
                        source_phc=src,
                        destination_phc=dst,
                        rejection_count=len(entries),
                        reason=f"Repeated safety rejections ({len(entries)}x ROUTE_UNSAFE)",
                        blocked_at=latest_ts.isoformat(),
                        expires_at=expires_at.isoformat(),
                        active=is_active,
                    )
                )

        return blocked_records

    def get_active_blocked_route_pairs(self) -> List[Tuple[str, str]]:
        """Return active blocked route tuples (source, destination) for optimizer constraints."""
        records = self.get_blocked_routes()
        return [(r.source_phc, r.destination_phc) for r in records if r.active]

    def get_ledger_summary(self) -> Dict[str, Any]:
        """Compile ledger statistics and human-in-the-loop learning state."""
        blocked_routes = self.get_blocked_routes()
        active_blocks = [b for b in blocked_routes if b.active]

        entries_view = [
            {
                "entry_id": e.entry_id,
                "plan_id": e.plan_id,
                "transfer_id": e.transfer_id,
                "ai_recommendation": e.ai_recommendation,
                "human_override": e.human_override,
                "reason": e.reason_code or "N/A",
                "notes": e.notes,
                "outcome": e.outcome,
                "timestamp": e.timestamp,
            }
            for e in self.ledger[-20:]
        ]

        return {
            "simulation_result": True,
            "engine": "Human-in-the-Loop Operational Constraint Learning",
            "disclaimer": "Verifiable operational rule learning based on empirical human feedback. Does not claim machine learning unless a statistical model is trained.",
            "total_entries": len(self.ledger),
            "rejections_count": sum(1 for e in self.ledger if e.human_decision == "REJECT"),
            "edits_count": sum(1 for e in self.ledger if e.human_decision == "EDIT"),
            "approvals_count": sum(1 for e in self.ledger if e.human_decision == "APPROVE"),
            "blocked_routes_policy": {
                "rule": f"Route rejected >= {self.block_threshold} times with ROUTE_UNSAFE marked temporarily blocked.",
                "duration_hours": self.block_duration_hours,
                "active_blocked_routes_count": len(active_blocks),
                "active_blocked_routes": [asdict(b) for b in active_blocks],
            },
            "recent_regret_ledger": entries_view,
        }
