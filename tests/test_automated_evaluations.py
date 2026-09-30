"""Test suite for Phase 15: HippoGrid Automated Evaluations (E1-E6).
Healthcare Infrastructure & Primary-care Planning Optimization Grid
"""
from pathlib import Path
import pytest
from scripts.run_evaluations import (
    run_experiment_e1,
    run_experiment_e2,
    run_experiment_e3,
    run_experiment_e4,
    run_experiment_e5,
    run_experiment_e6,
)


def test_experiment_e1_alerts():
    e1 = run_experiment_e1()
    assert e1["simulation_result"] is True
    res = e1["results"]
    assert res["sch_alerts"]["mean_lead_time_hours"] > res["stock_alerts"]["mean_lead_time_hours"]
    assert res["sch_alerts"]["recall"] > res["stock_alerts"]["recall"]


def test_experiment_e2_conformal():
    e2 = run_experiment_e2()
    assert e2["simulation_result"] is True
    res = e2["results"]
    assert "split_conformal_prediction" in res
    assert "raw_gaussian_heuristic" in res
    assert res["split_conformal_prediction"]["empirical_coverage"] >= 0.85


def test_experiment_e3_prescriber():
    e3 = run_experiment_e3()
    assert e3["simulation_result"] is True
    res = e3["results"]
    assert res["assurance_aware"]["remote_phc_protection_pct"] == 100.0
    assert res["assurance_aware"]["service_failure_probability"] < res["no_intervention"]["service_failure_probability"]


def test_experiment_e4_reverse_stress():
    e4 = run_experiment_e4()
    assert e4["simulation_result"] is True
    res = e4["results"]
    assert "evolutionary_search" in res
    assert "random_search" in res
    assert res["evolutionary_search"]["smallest_breach_shock_norm"] <= res["random_search"]["smallest_breach_shock_norm"]


def test_experiment_e5_federated():
    e5 = run_experiment_e5()
    assert e5["simulation_result"] is True
    res = e5["results"]
    assert res["federated"]["mae"] < res["local"]["mae"]


def test_experiment_e6_ablation():
    e6 = run_experiment_e6()
    assert e6["simulation_result"] is True
    res = e6["results"]
    assert len(res) == 6
    # Full HippoGrid must have lowest relative risk
    assert res[0]["relative_risk"] == 1.0
    for item in res[1:]:
        assert item["relative_risk"] > 1.0


def test_results_markdown_exists():
    md_path = Path("docs/RESULTS.md")
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "Simulation result" in content
    assert "Limitations" in content
