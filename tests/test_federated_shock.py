"""Test suite for Phase 13: HippoGrid Federated Shock Response.
Healthcare Infrastructure & Primary-care Planning Optimization Grid
"""
import pytest
from backend.federated.fed_avg import HippoGridFederatedEngine


def test_federated_engine_initialization():
    engine = HippoGridFederatedEngine()
    data = engine.load_prepared_datasets()
    assert "client_A" in data
    assert "client_B" in data
    assert "client_C_train" in data
    assert "client_C_test" in data

    X_A, y_A = data["client_A"]
    assert len(X_A) > 1000
    assert X_A.shape[1] == 5


def test_federated_training_and_comparison():
    engine = HippoGridFederatedEngine(seed=42)
    report = engine.train_and_compare(num_rounds=10, local_epochs=5)

    assert report["simulation_result"] is True
    assert report["rounds"] == 10
    assert report["parameter_count"] == 6  # 5 weights + 1 bias
    assert len(report["convergence"]) == 10

    results = report["results"]
    assert "local" in results
    assert "centralized" in results
    assert "federated" in results

    # Federated model must outperform isolated local model on State C flood test set
    assert results["federated"]["mae"] < results["local"]["mae"]
    assert results["federated"]["improvement_over_local_pct"] > 30.0
