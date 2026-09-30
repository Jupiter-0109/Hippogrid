"""HippoGrid Service Capability Horizon (SCH) Calculator.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

IMPORTANT NOTICE:
All dependency mappings are PROPOSED prototype assumptions.
Do not claim clinical validation.

Computes:
SCH(service, phc) = minimum time until any required dependency falls below the threshold.
- Drug time-to-depletion
- Staff time-to-threshold
- Bed time-to-capacity
- Power backup horizon
- Road-access impact on replenishment

Status Bounds:
- HEALTHY  >= 72h
- WATCH    = 48h to <72h
- CRITICAL < 48h
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from backend.sch.service_graph import ServiceCapabilityGraph, ServiceCapabilityNode


@dataclass
class DependencyHorizon:
    dependency_name: str
    category: str  # drugs, staff, beds, power, road_access
    horizon_hours: float
    details: str


@dataclass
class ServiceCapabilityAssessment:
    phc_id: str
    service: str
    sch_hours: float
    status: str  # HEALTHY, WATCH, CRITICAL
    limiting_dependency: str
    next_limiting_dependency: str
    dependency_horizons: List[DependencyHorizon] = field(default_factory=list)


class ServiceCapabilityHorizonCalculator:
    """Computes multi-dependency SCH horizons for PHC facilities."""

    def __init__(self, graph: Optional[ServiceCapabilityGraph] = None) -> None:
        self.graph = graph or ServiceCapabilityGraph()

    def calculate_drug_horizon(
        self,
        stock: float,
        demand_per_hour: float,
        road_blocked: bool = False,
        replenishment_lead_hours: float = 24.0,
    ) -> float:
        """Calculate drug time-to-depletion.
        Example: stock = 100, demand = 2/hour -> horizon = 50 hours.
        If road closure blocks replenishment, incoming stock cannot arrive.
        """
        if demand_per_hour <= 0:
            return 168.0  # nominal 1 week maximum horizon

        depletion_hours = stock / demand_per_hour

        # If road is blocked, replenishment is prevented from arriving
        if road_blocked:
            # Cannot be replenished; capped strictly at existing stock depletion
            return round(depletion_hours, 1)

        return round(depletion_hours, 1)

    def calculate_staff_horizon(
        self,
        nurses_on_duty: int,
        anms_on_duty: int,
        min_nurses_required: int,
        min_anms_required: int,
        shift_hours_remaining: float = 12.0,
        staff_absenteeism_risk: float = 0.0,
    ) -> float:
        """Calculate staff time-to-threshold before minimum staffing breaks down."""
        if nurses_on_duty < min_nurses_required or anms_on_duty < min_anms_required:
            return 0.0  # Already below critical staffing threshold!

        # Nominal shift duration remaining before next relief is required
        # If absenteeism risk is high, relief arrival is degraded
        risk_factor = max(1.0, 1.0 + staff_absenteeism_risk * 2.0)
        horizon = (shift_hours_remaining * (nurses_on_duty / max(1, min_nurses_required))) * (24.0 / (shift_hours_remaining * risk_factor))
        return round(min(168.0, max(0.0, horizon)), 1)

    def calculate_bed_horizon(
        self,
        occupied_beds: int,
        total_beds: int,
        admission_rate_per_hour: float,
    ) -> float:
        """Calculate bed time-to-capacity before inpatient bed saturation."""
        if total_beds <= 0 or occupied_beds >= total_beds:
            return 0.0  # 100% capacity reached

        available_beds = total_beds - occupied_beds
        if admission_rate_per_hour <= 0:
            return 168.0

        horizon = available_beds / admission_rate_per_hour
        return round(min(168.0, max(0.0, horizon)), 1)

    def calculate_power_horizon(
        self,
        grid_available: bool,
        battery_charge_percent: float,
        generator_fuel_liters: float,
        burn_rate_liters_per_hour: float = 2.2,
        battery_discharge_hours: float = 8.0,
    ) -> float:
        """Calculate electrical continuity backup horizon."""
        battery_hours = (battery_charge_percent / 100.0) * battery_discharge_hours
        fuel_hours = generator_fuel_liters / max(0.1, burn_rate_liters_per_hour)
        total_backup_hours = battery_hours + fuel_hours

        if grid_available:
            # Nominal grid uptime + stored backup
            return round(min(168.0, 72.0 + total_backup_hours), 1)
        else:
            # Grid offline: strictly limited to stored backup
            return round(max(0.0, total_backup_hours), 1)

    def calculate_road_access_horizon(
        self,
        road_status: str,
        travel_time_minutes: float,
        normal_travel_time_minutes: float = 45.0,
    ) -> float:
        """Calculate logistics and emergency referral access horizon."""
        if road_status == "BLOCKED":
            return 0.0  # Road impassable: zero referral/replenishment buffer!
        elif road_status == "DEGRADED":
            delay_ratio = travel_time_minutes / max(1.0, normal_travel_time_minutes)
            return round(max(6.0, 72.0 / delay_ratio), 1)
        else:
            return 168.0  # Open road: nominal continuity

    def compute_sch(
        self,
        phc_id: str,
        service_id: str,
        telemetry: Dict[str, Any],
    ) -> ServiceCapabilityAssessment:
        """Compute SCH(service, phc) = min time until any required dependency breaks."""
        service_node = self.graph.get_service(service_id)
        if not service_node:
            raise ValueError(f"Service '{service_id}' not found in service capability graph.")

        horizons: List[DependencyHorizon] = []

        # 1. Road Access Horizon
        road_status = telemetry.get("road_status", "OPEN")
        travel_time = float(telemetry.get("travel_time_minutes", 45.0))
        road_h = self.calculate_road_access_horizon(road_status, travel_time)
        horizons.append(DependencyHorizon("road_access", "road_access", road_h, f"Road status: {road_status}"))
        is_road_blocked = (road_status == "BLOCKED")

        # 2. Drug Horizons
        stocks = telemetry.get("drug_stocks", {})
        demands = telemetry.get("drug_demands_per_hour", {})
        for drug_dep in service_node.drugs:
            # Match directly or by case-insensitive / partial match (e.g. "ORS" in "MED-ORS-20.5G")
            cur_stock = None
            demand_hr = None
            for k, v in stocks.items():
                if k == drug_dep.id or drug_dep.id.lower() in k.lower() or k.lower() in drug_dep.id.lower():
                    cur_stock = float(v)
                    break
            for k, v in demands.items():
                if k == drug_dep.id or drug_dep.id.lower() in k.lower() or k.lower() in drug_dep.id.lower():
                    demand_hr = float(v)
                    break

            if cur_stock is None:
                cur_stock = float(drug_dep.critical_reserve * 5.0)
            if demand_hr is None:
                demand_hr = 1.0

            d_h = self.calculate_drug_horizon(cur_stock, demand_hr, road_blocked=is_road_blocked)
            horizons.append(
                DependencyHorizon(
                    f"drug_{drug_dep.id}",
                    "drugs",
                    d_h,
                    f"Stock: {cur_stock}, Demand: {demand_hr}/h, Road blocked: {is_road_blocked}",
                )
            )

        # 3. Staff Horizon
        nurses = int(telemetry.get("nurse_on_duty", 2))
        anms = int(telemetry.get("anm_on_duty", 2))
        absenteeism = float(telemetry.get("absenteeism_rate", 0.05))
        staff_h = self.calculate_staff_horizon(
            nurses,
            anms,
            service_node.staff.min_nurses,
            service_node.staff.min_anms,
            shift_hours_remaining=float(telemetry.get("shift_hours_remaining", 10.0)),
            staff_absenteeism_risk=absenteeism,
        )
        horizons.append(
            DependencyHorizon(
                "staff",
                "staff",
                staff_h,
                f"Nurses: {nurses}/{service_node.staff.min_nurses}, ANMs: {anms}/{service_node.staff.min_anms}",
            )
        )

        # 4. Bed Horizon (if required)
        if service_node.beds.requires_inpatient_beds:
            total_b = int(telemetry.get("total_beds", 6))
            occ_b = int(telemetry.get("occupied_beds", 2))
            admiss_hr = float(telemetry.get("bed_admissions_per_hour", 0.0))
            bed_h = self.calculate_bed_horizon(occ_b, total_b, admiss_hr)
            horizons.append(DependencyHorizon("beds", "beds", bed_h, f"Beds: {occ_b}/{total_b} occupied"))

        # 5. Power Horizon (if required)
        grid_on = bool(telemetry.get("grid_available", True))
        bat_pct = float(telemetry.get("battery_charge_percent", 100.0))
        fuel_l = float(telemetry.get("generator_fuel_liters", 80.0))
        power_h = self.calculate_power_horizon(grid_on, bat_pct, fuel_l)
        horizons.append(
            DependencyHorizon(
                "power",
                "power",
                power_h,
                f"Grid: {grid_on}, Battery: {bat_pct}%, Fuel: {fuel_l}L",
            )
        )

        # Sort horizons ascending to identify limiting and next limiting dependencies
        horizons_sorted = sorted(horizons, key=lambda x: x.horizon_hours)

        limiting = horizons_sorted[0]
        next_limiting = horizons_sorted[1] if len(horizons_sorted) > 1 else limiting
        min_sch = limiting.horizon_hours

        # Status assignment:
        # HEALTHY >= 72h, WATCH = 48h to <72h, CRITICAL < 48h
        if min_sch >= 72.0:
            status = "HEALTHY"
        elif min_sch >= 48.0:
            status = "WATCH"
        else:
            status = "CRITICAL"

        return ServiceCapabilityAssessment(
            phc_id=phc_id,
            service=service_id,
            sch_hours=round(min_sch, 1),
            status=status,
            limiting_dependency=limiting.dependency_name,
            next_limiting_dependency=next_limiting.dependency_name,
            dependency_horizons=horizons,
        )
