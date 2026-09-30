"""Test suite for Phase 14: HippoGrid Regret Ledger & Operational Constraints.
Healthcare Infrastructure & Primary-care Planning Optimization Grid
"""
from datetime import datetime, timedelta
import pytest
from backend.feedback.regret_ledger import RegretLedgerEngine


def test_regret_ledger_recording_and_blocking_policy():
    engine = RegretLedgerEngine(block_threshold=3, block_duration_hours=72)
    # Clear seeded initial entries for deterministic isolated test
    engine.ledger = []

    # Record 2 ROUTE_UNSAFE rejections on route PHC-01 -> PHC-02
    engine.record_decision(
        plan_id="plan-test-1",
        transfer_id="tr-1",
        source_phc="PHC-TEST-01",
        destination_phc="PHC-TEST-02",
        medicine="ORS",
        original_quantity=30,
        human_decision="REJECT",
        reason_code="ROUTE_UNSAFE",
        notes="Bridge submerged",
    )
    engine.record_decision(
        plan_id="plan-test-2",
        transfer_id="tr-2",
        source_phc="PHC-TEST-01",
        destination_phc="PHC-TEST-02",
        medicine="ORS",
        original_quantity=30,
        human_decision="REJECT",
        reason_code="ROUTE_UNSAFE",
        notes="Rockslide blocking lane",
    )

    # After 2 rejections, route must NOT be blocked yet
    active_blocked = engine.get_active_blocked_route_pairs()
    assert ("PHC-TEST-01", "PHC-TEST-02") not in active_blocked

    # Record 3rd ROUTE_UNSAFE rejection
    engine.record_decision(
        plan_id="plan-test-3",
        transfer_id="tr-3",
        source_phc="PHC-TEST-01",
        destination_phc="PHC-TEST-02",
        medicine="ORS",
        original_quantity=30,
        human_decision="REJECT",
        reason_code="ROUTE_UNSAFE",
        notes="Flooded culvert confirmed by local police",
    )

    # After 3rd rejection, route MUST be marked as temporarily blocked
    blocked_records = engine.get_blocked_routes()
    assert len(blocked_records) == 1
    assert blocked_records[0].route_key == "PHC-TEST-01->PHC-TEST-02"
    assert blocked_records[0].rejection_count == 3
    assert blocked_records[0].active is True
    assert "expires_at" in blocked_records[0].__dict__

    # Verify active blocked pairs for optimizer
    active_pairs = engine.get_active_blocked_route_pairs()
    assert ("PHC-TEST-01", "PHC-TEST-02") in active_pairs


def test_regret_ledger_edit_override():
    engine = RegretLedgerEngine()
    entry = engine.record_decision(
        plan_id="plan-test-4",
        transfer_id="tr-4",
        source_phc="PHC-TEST-03",
        destination_phc="PHC-TEST-04",
        medicine="oxytocin",
        original_quantity=40,
        human_decision="EDIT",
        modified_quantity=25,
        reason_code="STOCK_RESERVED",
        notes="Reserved 15 for local labor room",
    )

    assert entry.outcome == "PARAMETRIC_OVERRIDE_TO_25"
    assert entry.human_override["modified_quantity"] == 25
