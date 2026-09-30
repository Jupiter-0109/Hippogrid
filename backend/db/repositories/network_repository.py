"""Repository for administrative network hierarchy and master tables."""
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.db.models import District, Medicine, PHC, Service, ServiceDependency, State, Warehouse
from backend.db.repositories.base import BaseRepository


class NetworkRepository:
    """Repository handling State, District, PHC, Warehouse, Service, and Medicine operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # States
    def list_states(self) -> List[State]:
        return self.db.query(State).order_by(State.code).all()

    def get_state_by_code(self, code: str) -> Optional[State]:
        return self.db.query(State).filter(State.code == code).first()

    # Districts
    def list_districts(self, state_id: Optional[str] = None) -> List[District]:
        q = self.db.query(District)
        if state_id:
            q = q.filter(District.state_id == state_id)
        return q.order_by(District.code).all()

    def get_district_by_code(self, code: str) -> Optional[District]:
        return self.db.query(District).filter(District.code == code).first()

    # PHCs
    def list_phcs(self, district_id: Optional[str] = None) -> List[PHC]:
        q = self.db.query(PHC)
        if district_id:
            q = q.filter(PHC.district_id == district_id)
        return q.order_by(PHC.code).all()

    def get_phc_by_code(self, code: str) -> Optional[PHC]:
        return self.db.query(PHC).filter(PHC.code == code).first()

    # Warehouses
    def list_warehouses(self, district_id: Optional[str] = None) -> List[Warehouse]:
        q = self.db.query(Warehouse)
        if district_id:
            q = q.filter(Warehouse.district_id == district_id)
        return q.order_by(Warehouse.code).all()

    # Services
    def list_services(self) -> List[Service]:
        return self.db.query(Service).order_by(Service.id).all()

    def get_service_dependencies(self, service_id: str) -> List[ServiceDependency]:
        return self.db.query(ServiceDependency).filter(ServiceDependency.service_id == service_id).all()

    # Medicines
    def list_medicines(self) -> List[Medicine]:
        return self.db.query(Medicine).order_by(Medicine.id).all()
