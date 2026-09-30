"""HippoGrid Network Topology Definitions.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Defines the 3-state, 6-district, 36-PHC, 6-warehouse network hierarchy,
clinical service lines, essential medicines, and inter-facility transit topology.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np


@dataclass(frozen=True)
class StateDef:
    code: str
    name: str
    start_date: str
    end_date: str
    flood_event_cap: int = 999  # State C capped at 2


@dataclass(frozen=True)
class DistrictDef:
    code: str
    name: str
    state_code: str
    headquarters: str
    base_lat: float
    base_lon: float


@dataclass
class PhcDef:
    code: str
    name: str
    district_code: str
    state_code: str
    latitude: float
    longitude: float
    catchment_population: int
    remote_flag: bool
    vulnerability_score: float
    total_beds: int
    staff_mo: int
    staff_nurse: int
    staff_anm: int
    backup_power_type: str
    backup_power_capacity_kva: float
    backup_power_hours: float
    solar_capacity_kw: float


@dataclass
class WarehouseDef:
    code: str
    name: str
    district_code: str
    state_code: str
    latitude: float
    longitude: float
    cold_chain_capacity_liters: float
    dry_storage_capacity_sqm: float


@dataclass(frozen=True)
class ServiceDef:
    id: str
    name: str
    category: str
    criticality: str
    min_staff_required: int
    requires_uninterrupted_power: bool


@dataclass(frozen=True)
class MedicineDef:
    id: str
    name: str
    category: str
    unit: str
    is_cold_chain_required: bool
    min_temp_celsius: float | None
    max_temp_celsius: float | None
    driven_by_patient_metric: str
    units_per_case: float


def build_network_topology(seed: int = 42) -> Tuple[
    List[StateDef],
    List[DistrictDef],
    List[PhcDef],
    List[WarehouseDef],
    List[ServiceDef],
    List[MedicineDef],
]:
    """Deterministically construct network hierarchy for 3 states, 6 districts, 36 PHCs, and 6 warehouses."""
    rng = np.random.default_rng(seed)

    # 1. States (3)
    # State A: 18 months (2024-01-01 to 2025-06-30)
    # State B: 12 months beginning 2024-07-01 to 2025-06-30
    # State C: 18 months (2024-01-01 to 2025-06-30) with lower disaster history (2 flood events)
    states = [
        StateDef(code="STA", name="State A (Highland Region)", start_date="2024-01-01", end_date="2025-06-30"),
        StateDef(code="STB", name="State B (Riverine Valley)", start_date="2024-07-01", end_date="2025-06-30"),
        StateDef(code="STC", name="State C (Plateau Corridor)", start_date="2024-01-01", end_date="2025-06-30", flood_event_cap=2),
    ]

    # 2. Districts (6 - exactly 2 per state)
    districts = [
        DistrictDef(code="DST-A1", name="North Aranya District", state_code="STA", headquarters="Aranya City", base_lat=24.5854, base_lon=73.7125),
        DistrictDef(code="DST-A2", name="South Devgarh District", state_code="STA", headquarters="Devgarh Town", base_lat=24.1200, base_lon=73.9500),
        DistrictDef(code="DST-B1", name="East Barani District", state_code="STB", headquarters="Barani Central", base_lat=23.8340, base_lon=74.3120),
        DistrictDef(code="DST-B2", name="West Kusuma District", state_code="STB", headquarters="Kusuma Hub", base_lat=23.4500, base_lon=74.6000),
        DistrictDef(code="DST-C1", name="Chinar Ridge District", state_code="STC", headquarters="Chinar Fort", base_lat=25.2100, base_lon=75.1200),
        DistrictDef(code="DST-C2", name="Dharani Plain District", state_code="STC", headquarters="Dharani Junction", base_lat=25.6500, base_lon=75.5400),
    ]

    # 3. Warehouses (6 - exactly 1 per district)
    warehouses = []
    for d in districts:
        w_code = f"WH-{d.code}"
        warehouses.append(
            WarehouseDef(
                code=w_code,
                name=f"{d.name} Central Medical Depot",
                district_code=d.code,
                state_code=d.state_code,
                latitude=round(d.base_lat + 0.015, 6),
                longitude=round(d.base_lon + 0.015, 6),
                cold_chain_capacity_liters=15000.0,
                dry_storage_capacity_sqm=750.0,
            )
        )

    # 4. PHCs (36 - exactly 6 per district)
    phcs = []
    for d_idx, d in enumerate(districts):
        for p_idx in range(1, 7):
            phc_code = f"PHC-{d.code}-{p_idx:02d}"
            # Sub-offsets for geographical dispersion (approx 10-35km from district HQ)
            angle = (p_idx / 6.0) * 2 * np.pi + rng.uniform(-0.15, 0.15)
            dist_deg = rng.uniform(0.12, 0.35)
            lat = round(d.base_lat + dist_deg * np.cos(angle), 6)
            lon = round(d.base_lon + dist_deg * np.sin(angle), 6)

            # Remoteness: outer indices or stochastic draw
            is_remote = bool(p_idx in (5, 6) or (rng.uniform(0, 1) < 0.25))
            
            # Catchment population
            pop = int(rng.normal(32000, 5000)) if not is_remote else int(rng.normal(24000, 3500))
            pop = max(18000, min(52000, pop))

            # Total beds: 4 to 10
            beds = int(rng.choice([4, 6, 6, 6, 8, 10]))
            if is_remote and beds > 6:
                beds = 6

            # Staff allocations
            mo = int(rng.choice([1, 1, 2])) if not is_remote else 1
            nurse = int(rng.choice([2, 3, 4])) if not is_remote else 2
            anm = int(rng.choice([2, 3, 4]))

            # Vulnerability score (composite 1.0 to 4.5)
            vuln = 1.0 + (1.2 if is_remote else 0.3) + float(rng.uniform(0.1, 1.2))
            if d.state_code == "STC":
                vuln = max(1.0, vuln - 0.5)  # Lower disaster history for State C
            vuln = round(vuln, 2)

            # Power backup
            backup_type = "DIESEL_GENERATOR" if not is_remote else "HYBRID_SOLAR_DIESEL"
            backup_hours = 24.0 if not is_remote else 36.0
            kva = float(rng.choice([15.0, 20.0, 25.0]))
            solar = float(rng.choice([3.0, 5.0, 8.0])) if is_remote else float(rng.choice([0.0, 2.5, 5.0]))

            phcs.append(
                PhcDef(
                    code=phc_code,
                    name=f"PHC {d.name.split()[0]} Sector-{p_idx}",
                    district_code=d.code,
                    state_code=d.state_code,
                    latitude=lat,
                    longitude=lon,
                    catchment_population=pop,
                    remote_flag=is_remote,
                    vulnerability_score=vuln,
                    total_beds=beds,
                    staff_mo=mo,
                    staff_nurse=nurse,
                    staff_anm=anm,
                    backup_power_type=backup_type,
                    backup_power_capacity_kva=kva,
                    backup_power_hours=backup_hours,
                    solar_capacity_kw=solar,
                )
            )

    # 5. Core Clinical Services (Exact 4 Services)
    services = [
        ServiceDef("diarrhoeal_care", "Diarrhoeal Disease Management & Oral Rehydration", "ACUTE_CARE", "CRITICAL", 1, False),
        ServiceDef("maternal_delivery", "Maternal Care & Normal Delivery", "MATERNAL", "CRITICAL", 2, True),
        ServiceDef("vaccination", "Routine Immunization & Cold Chain", "PREVENTIVE", "CRITICAL", 1, True),
        ServiceDef("fever_malaria", "Fever & Malaria Case Management", "INFECTIOUS", "HIGH", 1, False),
    ]

    # 6. Essential Medicines (Exact 8 Medicines)
    medicines = [
        MedicineDef("ORS", "Oral Rehydration Salts (ORS)", "REHYDRATION", "SACHET", False, None, None, "diarrhoeal_cases", 3.0),
        MedicineDef("IV_fluids", "Intravenous Ringer Lactate / Normal Saline", "IV_FLUID", "BOTTLE", False, None, None, "emergency_cases", 1.8),
        MedicineDef("zinc", "Zinc Sulfate 20mg Dispersible Tablets", "SUPPLEMENT", "STRIP", False, None, None, "diarrhoeal_cases", 2.0),
        MedicineDef("oxytocin", "Oxytocin Injection 10 IU", "UTEROTONIC", "AMPOULE", True, 2.0, 8.0, "deliveries", 2.0),
        MedicineDef("paracetamol", "Paracetamol 500mg Tablets", "ANTIPYRETIC", "STRIP", False, None, None, "fever_cases", 1.5),
        MedicineDef("ACT_antimalarial", "Artemisinin-based Combination Therapy (ACT)", "ANTIMALARIAL", "STRIP", False, None, None, "fever_cases", 0.6),
        MedicineDef("vaccine_penta", "Pentavalent Vaccine (DTP-HepB-Hib)", "VACCINE", "VIAL", True, 2.0, 8.0, "deliveries", 1.0),
        MedicineDef("amlodipine", "Amlodipine 5mg Tablets", "CARDIOVASCULAR", "STRIP", False, None, None, "opd_cases", 0.4),
    ]

    return states, districts, phcs, warehouses, services, medicines
