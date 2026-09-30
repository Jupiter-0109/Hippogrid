"""Federated Learning API Router.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Endpoints:
- GET /api/v1/federated/evaluate: Retrieve multi-state FedAvg evaluation vs Local & Centralized.
- POST /api/v1/federated/train: Execute 10-round FedAvg training session across State A, B, and C.
"""
from typing import Any, Dict
from fastapi import APIRouter
from backend.federated.fed_avg import HippoGridFederatedEngine

router = APIRouter(prefix="/api/v1/federated", tags=["federated-learning"])
ENGINE = HippoGridFederatedEngine()


@router.get("/evaluate")
def evaluate_federated_models() -> Dict[str, Any]:
    """Compare Local vs Centralized vs Federated FedAvg models on held-out State C flood events."""
    return ENGINE.train_and_compare(num_rounds=10)


@router.post("/train")
def trigger_federated_training(rounds: int = 10) -> Dict[str, Any]:
    """Execute federated parameter aggregation run across participating state clients."""
    num_rounds = min(max(rounds, 1), 30)
    return ENGINE.train_and_compare(num_rounds=num_rounds)
