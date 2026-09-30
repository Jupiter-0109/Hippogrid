"""Repository for operational telemetry, inventory transactions, and service continuity."""
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.db.models import (
    BedStatus,
    InventoryTransaction,
    PatientVisit,
    PowerStatus,
    RoadStatus,
    ServiceContinuity,
    WeatherObservation,
    WorkforceStatus,
)


class TelemetryRepository:
    """Repository handling telemetry inserts, queries, and continuity assessments."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # Inventory Transactions
    def record_inventory_transaction(
        self,
        phc_id: Any,
        medicine_id: str,
        quantity_change: float,
        stock_after: float,
        transaction_type: str,
    ) -> InventoryTransaction:
        tx = InventoryTransaction(
            phc_id=phc_id,
            medicine_id=medicine_id,
            quantity_change=quantity_change,
            stock_after=stock_after,
            transaction_type=transaction_type,
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def get_latest_inventory_stock(self, phc_id: Any, medicine_id: str) -> Optional[float]:
        latest_tx = (
            self.db.query(InventoryTransaction)
            .filter(
                InventoryTransaction.phc_id == phc_id,
                InventoryTransaction.medicine_id == medicine_id,
            )
            .order_by(InventoryTransaction.recorded_at.desc())
            .first()
        )
        return float(latest_tx.stock_after) if latest_tx else None

    # Patient Visits
    def record_patient_visits(self, phc_id: Any, service_id: str, count: int) -> PatientVisit:
        visit = PatientVisit(phc_id=phc_id, service_id=service_id, visit_count=count)
        self.db.add(visit)
        self.db.commit()
        self.db.refresh(visit)
        return visit

    # Service Continuity
    def get_phc_continuity(self, phc_id: Any) -> List[ServiceContinuity]:
        return (
            self.db.query(ServiceContinuity)
            .filter(ServiceContinuity.phc_id == phc_id)
            .order_by(ServiceContinuity.hours_to_compromise.asc())
            .all()
        )

    def upsert_service_continuity(
        self,
        phc_id: Any,
        service_id: str,
        status: str,
        hours_to_compromise: float,
        primary_bottleneck: str,
    ) -> ServiceContinuity:
        record = (
            self.db.query(ServiceContinuity)
            .filter(
                ServiceContinuity.phc_id == phc_id,
                ServiceContinuity.service_id == service_id,
            )
            .first()
        )
        if record:
            record.status = status
            record.hours_to_compromise = hours_to_compromise
            record.primary_bottleneck = primary_bottleneck
        else:
            record = ServiceContinuity(
                phc_id=phc_id,
                service_id=service_id,
                status=status,
                hours_to_compromise=hours_to_compromise,
                primary_bottleneck=primary_bottleneck,
            )
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
