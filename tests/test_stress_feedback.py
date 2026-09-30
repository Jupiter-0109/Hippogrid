"""Comprehensive Tests for Phase 9 (Reverse Stress Engine)
and Phase 10 (Human-in-the-Loop Review).

Verifications:
1. Reverse Stress: Answer Question "What is the smallest plausible compound shock that causes at least 3 PHCs to lose an essential service for 48 continuous hours?"
2. Normalized shock size and plausibility calculations.
3. Resilience Frontier generation comparing without vs with HippoGrid intervention.
4. PHC Fragility Ranking across 36 health centres.
5. Human Review validation:
   - APPROVE action
   - EDIT action stores original_quantity and modified_quantity
   - REJECT action strictly enforces reason code (ROUTE_UNSAFE, etc.)
   - Audit trail persistence and summary generation
   - Explicit mandate: No false claims of automatic learning without real learning rules
"""
import pytest
from backend.feedback.review import (
    HumanAction,
    HumanReviewEngine,
    RejectionReasonCode,
    ReviewItem,
)
from backend.stress.reverse_stress import CompoundShock, ReverseStressEngine


@pytest.fixture
def stress_engine():
    return ReverseStressEngine(seed=42)


@pytest.fixture
def review_engine():
    return HumanReviewEngine()


def test_normalized_shock_size_and_plausibility(stress_engine):
    """Test normalized shock size in [0, 1] and plausibility decay."""
    # Zero shock
    zero_size = stress_engine.calculate_normalized_shock_size(
        rain=1.0, road=0.0, staff=0.0, demand=1.0
    )
    assert zero_size == 0.0
    assert stress_engine.calculate_plausibility(zero_size) == 1.0

    # Intermediate compound shock
    med_size = stress_engine.calculate_normalized_shock_size(
        rain=2.5, road=0.4, staff=0.35, demand=2.0
    )
    assert 0.40 <= med_size <= 0.70
    plaus = stress_engine.calculate_plausibility(med_size)
    assert 0.0 < plaus < 1.0


def test_reverse_stress_evaluation_and_frontier(stress_engine):
    """Test reverse stress condition: 3 PHCs lose service for 48h."""
    frontier = stress_engine.compute_resilience_frontier(n_candidates=6)

    assert len(frontier) == 6
    for pt in frontier:
        assert 0.0 <= pt.shock_size <= 1.0
        assert 0.0 <= pt.plausibility <= 1.0
        assert 0.0 <= pt.failure_probability_without_intervention <= 1.0
        assert 0.0 <= pt.failure_probability_with_intervention <= 1.0
        # HippoGrid intervention should cut failure probability significantly
        assert pt.failure_probability_with_intervention <= pt.failure_probability_without_intervention


def test_phc_fragility_ranking(stress_engine):
    """Test fragility ranking across all 36 PHCs."""
    ranking = stress_engine.compute_fragility_ranking()

    assert len(ranking) == 36
    # Assure sorted descending by vulnerability
    for i in range(len(ranking) - 1):
        assert ranking[i].vulnerability_index >= ranking[i + 1].vulnerability_index
        assert ranking[i].rank == i + 1

    # Check top fragile attributes
    top_fragile = ranking[0]
    assert top_fragile.critical_service in ["diarrhoeal_care", "maternal_delivery"]
    assert top_fragile.breakdown_shock_size > 0


def test_reverse_stress_full_report(stress_engine):
    """Test full report generation and minimal compound shock discovery."""
    report = stress_engine.generate_full_report()

    assert "At least 3 PHCs" in report.target_condition
    assert "normalized_shock_size" in report.minimal_compound_shock
    assert len(report.critical_phcs) > 0
    assert len(report.critical_services) > 0
    assert report.comparison_summary["resilience_extension_percent"] > 0


def test_human_review_approval(review_engine):
    """Test APPROVE action creates proper audit entry."""
    reviews = [
        ReviewItem(
            transfer_id="TR-101",
            action=HumanAction.APPROVE,
            original_quantity=50,
        )
    ]
    entries = review_engine.validate_and_record_feedback(
        plan_id="PLN-2025-01",
        actor_id="cmo_dr_sharma",
        actor_role="Chief Medical Officer",
        reviews=reviews,
    )
    assert len(entries) == 1
    assert entries[0].action == "APPROVE"
    assert entries[0].original_quantity == 50
    assert entries[0].modified_quantity is None


def test_human_review_edit_preserves_both_quantities(review_engine):
    """Test EDIT action preserves original and modified quantity."""
    reviews = [
        ReviewItem(
            transfer_id="TR-102",
            action=HumanAction.EDIT,
            original_quantity=80,
            modified_quantity=45,
            notes="Reduced due to small transport carrier capacity",
        )
    ]
    entries = review_engine.validate_and_record_feedback(
        plan_id="PLN-2025-01",
        actor_id="cmo_dr_sharma",
        actor_role="Chief Medical Officer",
        reviews=reviews,
    )
    assert len(entries) == 1
    assert entries[0].action == "EDIT"
    assert entries[0].original_quantity == 80
    assert entries[0].modified_quantity == 45


def test_human_review_rejection_requires_reason(review_engine):
    """Test REJECT action strictly enforces reason code."""
    # Attempt reject without reason should raise ValueError
    bad_review = [
        ReviewItem(
            transfer_id="TR-103",
            action=HumanAction.REJECT,
            original_quantity=30,
            reason_code=None,  # Missing reason!
        )
    ]
    with pytest.raises(ValueError) as excinfo:
        review_engine.validate_and_record_feedback(
            plan_id="PLN-2025-01",
            actor_id="cmo_dr_sharma",
            actor_role="Chief Medical Officer",
            reviews=bad_review,
        )
    assert "explicit reason code" in str(excinfo.value)

    # Valid reject with ROUTE_UNSAFE
    valid_review = [
        ReviewItem(
            transfer_id="TR-103",
            action=HumanAction.REJECT,
            original_quantity=30,
            reason_code=RejectionReasonCode.ROUTE_UNSAFE,
            notes="Flash flood collapsed bridge on Sector-2 road",
        )
    ]
    entries = review_engine.validate_and_record_feedback(
        plan_id="PLN-2025-01",
        actor_id="cmo_dr_sharma",
        actor_role="Chief Medical Officer",
        reviews=valid_review,
    )
    assert entries[0].action == "REJECT"
    assert entries[0].reason_code == "ROUTE_UNSAFE"


def test_feedback_summary_compilation(review_engine):
    """Test feedback summary aggregates decisions and audit trail."""
    # Record sample feedback entries first
    reviews = [
        ReviewItem("TR-201", HumanAction.APPROVE, 50),
        ReviewItem("TR-202", HumanAction.EDIT, 60, 40),
        ReviewItem("TR-203", HumanAction.REJECT, 30, reason_code=RejectionReasonCode.ROUTE_UNSAFE),
    ]
    review_engine.validate_and_record_feedback("PLN-01", "dr_test", "CMO", reviews)

    summary = review_engine.get_feedback_summary()
    assert summary["total_decisions"] == 3
    assert summary["approved_count"] == 1
    assert summary["edited_count"] == 1
    assert summary["rejected_count"] == 1
    assert "ROUTE_UNSAFE" in summary["rejection_reasons_breakdown"]
    # Verify no false claim of automatic learning
    assert "governed by human sign-off" in summary["learning_status"]
