"""HippoGrid Service Capability Graph.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

IMPORTANT NOTICE:
All dependency mappings are PROPOSED prototype assumptions.
Do not claim clinical validation.

Represents services as directed capability dependency graphs connecting:
- Services: diarrhoeal_care, maternal_delivery, vaccination, fever_malaria
- Dependencies: drugs, staff, beds, power, road_access
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from backend.core.config import PROJECT_ROOT


@dataclass
class DrugDependency:
    id: str
    burn_rate_per_patient: float
    critical_reserve: float


@dataclass
class StaffDependency:
    min_nurses: int
    min_anms: int


@dataclass
class BedDependency:
    requires_inpatient_beds: bool
    admission_rate: float
    avg_bed_days: float


@dataclass
class PowerDependency:
    mandatory: bool
    min_backup_hours: float
    cold_chain_required: bool = False


@dataclass
class RoadDependency:
    max_transit_delay_hours: float
    replenishment_blockage_impact: bool = True


@dataclass
class ServiceCapabilityNode:
    id: str
    name: str
    category: str
    criticality: str
    drugs: List[DrugDependency]
    staff: StaffDependency
    beds: BedDependency
    power: PowerDependency
    road_access: RoadDependency


class ServiceCapabilityGraph:
    """Directed dependency graph loaded from config/service_map.yaml."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or (PROJECT_ROOT / "config" / "service_map.yaml")
        self.services: Dict[str, ServiceCapabilityNode] = {}
        self._load_graph()

    def _load_graph(self) -> None:
        if not self.config_path.exists():
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for item in data.get("services", []):
            deps = item.get("dependencies", {})

            # Drugs
            drugs = [
                DrugDependency(
                    id=d["id"],
                    burn_rate_per_patient=float(d.get("burn_rate_per_patient", 1.0)),
                    critical_reserve=float(d.get("critical_reserve", 10.0)),
                )
                for d in deps.get("drugs", [])
            ]

            # Staff
            staff_data = deps.get("staff", {})
            staff = StaffDependency(
                min_nurses=int(staff_data.get("min_nurses", 1)),
                min_anms=int(staff_data.get("min_anms", 0)),
            )

            # Beds
            beds_data = deps.get("beds", {})
            beds = BedDependency(
                requires_inpatient_beds=bool(beds_data.get("requires_inpatient_beds", False)),
                admission_rate=float(beds_data.get("admission_rate", 0.0)),
                avg_bed_days=float(beds_data.get("avg_bed_days", 0.0)),
            )

            # Power
            power_data = deps.get("power", {})
            power = PowerDependency(
                mandatory=bool(power_data.get("mandatory", False)),
                min_backup_hours=float(power_data.get("min_backup_hours", 6.0)),
                cold_chain_required=bool(power_data.get("cold_chain_required", False)),
            )

            # Road
            road_data = deps.get("road_access", {})
            road = RoadDependency(
                max_transit_delay_hours=float(road_data.get("max_transit_delay_hours", 12.0)),
                replenishment_blockage_impact=bool(road_data.get("replenishment_blockage_impact", True)),
            )

            node = ServiceCapabilityNode(
                id=item["id"],
                name=item["name"],
                category=item.get("category", "GENERAL"),
                criticality=item.get("criticality", "CRITICAL"),
                drugs=drugs,
                staff=staff,
                beds=beds,
                power=power,
                road_access=road,
            )
            self.services[node.id] = node

    def get_service(self, service_id: str) -> Optional[ServiceCapabilityNode]:
        return self.services.get(service_id)

    def list_services(self) -> List[ServiceCapabilityNode]:
        return list(self.services.values())
