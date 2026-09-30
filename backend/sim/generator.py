"""HippoGrid Synthetic Telemetry Generator.
Healthcare Infrastructure & Primary-care Planning Optimization Grid

Generates 18 months (2024-01-01 to 2025-06-30) of realistic, non-random daily
telemetry across 3 states, 6 districts, 36 PHCs, and 6 warehouses with:
- Weekly and yearly seasonality
- Monsoon rainfall & lagged disease outbreaks
- Population-scaled healthcare demand
- Demand-driven pharmaceutical inventory with replenishment lead times
- Zero negative stock guarantees
- Extreme weather road closures and travel time degradation
- Weather-induced power outages and fuel consumption
- Realistic missing telemetry (1-3%) and clinical outliers
- Strict seed 42 reproducibility
"""
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from backend.sim.network import (
    DistrictDef,
    MedicineDef,
    PhcDef,
    ServiceDef,
    StateDef,
    WarehouseDef,
    build_network_topology,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


class SyntheticDataGenerator:
    """Deterministic synthetic data generator for HippoGrid PHC network."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        (
            self.states,
            self.districts,
            self.phcs,
            self.warehouses,
            self.services,
            self.medicines,
        ) = build_network_topology(seed=seed)

        self.district_by_code: Dict[str, DistrictDef] = {d.code: d for d in self.districts}
        self.phc_by_code: Dict[str, PhcDef] = {p.code: p for p in self.phcs}

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """Generate all master and telemetry datasets."""
        # Reset RNG to guarantee exact reproducibility regardless of call order
        self.rng = np.random.default_rng(self.seed)

        df_states = self._generate_states_df()
        df_districts = self._generate_districts_df()
        df_phcs = self._generate_phcs_df()
        df_warehouses = self._generate_warehouses_df()
        df_services = self._generate_services_df()
        df_medicines = self._generate_medicines_df()

        df_weather = self._generate_weather_telemetry()
        df_power = self._generate_power_telemetry(df_weather)
        df_patient = self._generate_patient_telemetry(df_weather)
        df_workforce = self._generate_workforce_telemetry(df_weather)
        df_beds = self._generate_bed_telemetry(df_patient)
        df_inventory = self._generate_inventory_telemetry(df_patient, df_weather)
        df_roads = self._generate_road_telemetry(df_weather)

        # Inject realistic missing values (1% to 2.5%) into telemetry columns
        df_patient_clean = df_patient.copy()  # keep clean version for invariant tests
        df_weather = self._inject_missing_values(df_weather, ["rainfall_mm", "temperature_celsius"], 0.015)
        df_power = self._inject_missing_values(df_power, ["outage_hours", "grid_uptime_hours"], 0.02)
        df_patient = self._inject_missing_values(df_patient, ["opd_cases", "emergency_cases"], 0.018)
        df_workforce = self._inject_missing_values(df_workforce, ["absenteeism_rate"], 0.02)

        return {
            "states": df_states,
            "districts": df_districts,
            "phcs": df_phcs,
            "warehouses": df_warehouses,
            "services": df_services,
            "medicines": df_medicines,
            "weather": df_weather,
            "power": df_power,
            "patient": df_patient,
            "patient_clean": df_patient_clean,
            "workforce": df_workforce,
            "beds": df_beds,
            "inventory": df_inventory,
            "roads": df_roads,
        }

    # =========================================================================
    # Master Entity DataFrames
    # =========================================================================

    def _generate_states_df(self) -> pd.DataFrame:
        records = [
            {
                "code": s.code,
                "name": s.name,
                "start_date": s.start_date,
                "end_date": s.end_date,
                "flood_event_cap": s.flood_event_cap,
            }
            for s in self.states
        ]
        return pd.DataFrame(records)

    def _generate_districts_df(self) -> pd.DataFrame:
        records = [
            {
                "code": d.code,
                "name": d.name,
                "state_code": d.state_code,
                "headquarters": d.headquarters,
                "latitude": d.base_lat,
                "longitude": d.base_lon,
            }
            for d in self.districts
        ]
        return pd.DataFrame(records)

    def _generate_phcs_df(self) -> pd.DataFrame:
        records = [
            {
                "code": p.code,
                "name": p.name,
                "district_code": p.district_code,
                "state_code": p.state_code,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "catchment_population": p.catchment_population,
                "remote_flag": p.remote_flag,
                "vulnerability_score": p.vulnerability_score,
                "total_beds": p.total_beds,
                "staff_mo": p.staff_mo,
                "staff_nurse": p.staff_nurse,
                "staff_anm": p.staff_anm,
                "backup_power_type": p.backup_power_type,
                "backup_power_capacity_kva": p.backup_power_capacity_kva,
                "backup_power_hours": p.backup_power_hours,
                "solar_capacity_kw": p.solar_capacity_kw,
            }
            for p in self.phcs
        ]
        return pd.DataFrame(records)

    def _generate_warehouses_df(self) -> pd.DataFrame:
        records = [
            {
                "code": w.code,
                "name": w.name,
                "district_code": w.district_code,
                "state_code": w.state_code,
                "latitude": w.latitude,
                "longitude": w.longitude,
                "cold_chain_capacity_liters": w.cold_chain_capacity_liters,
                "dry_storage_capacity_sqm": w.dry_storage_capacity_sqm,
            }
            for w in self.warehouses
        ]
        return pd.DataFrame(records)

    def _generate_services_df(self) -> pd.DataFrame:
        records = [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "criticality": s.criticality,
                "min_staff_required": s.min_staff_required,
                "requires_uninterrupted_power": s.requires_uninterrupted_power,
            }
            for s in self.services
        ]
        return pd.DataFrame(records)

    def _generate_medicines_df(self) -> pd.DataFrame:
        records = [
            {
                "id": m.id,
                "name": m.name,
                "category": m.category,
                "unit": m.unit,
                "is_cold_chain_required": m.is_cold_chain_required,
                "min_temp_celsius": m.min_temp_celsius,
                "max_temp_celsius": m.max_temp_celsius,
                "driven_by_patient_metric": m.driven_by_patient_metric,
                "units_per_case": m.units_per_case,
            }
            for m in self.medicines
        ]
        return pd.DataFrame(records)

    # =========================================================================
    # Telemetry: Weather & Disasters
    # =========================================================================

    def _generate_weather_telemetry(self) -> pd.DataFrame:
        records = []
        full_date_range = pd.date_range("2024-01-01", "2025-06-30", freq="D")

        for d in self.districts:
            state = next(s for s in self.states if s.code == d.state_code)
            # Filter dates for district according to state's operational horizon
            dates = pd.date_range(state.start_date, state.end_date, freq="D")
            
            # State C is strictly capped at 2 major flood events across entire horizon
            is_state_c = (d.state_code == "STC")
            state_c_flood_dates = [pd.Timestamp("2024-08-14"), pd.Timestamp("2024-09-08")]
            
            for dt in dates:
                doy = dt.day_of_year
                # 1. Yearly Temperature curve (May peak 39C, Jan low 16C)
                temp_base = 27.5 + 11.0 * np.sin(2 * np.pi * (doy - 75) / 365.25)
                temp = round(float(temp_base + self.rng.normal(0, 1.8)), 2)

                # 2. Monsoon rainfall (July 1 to Sept 30 is DOY ~ 183 to 274)
                is_monsoon = (182 <= doy <= 273)
                
                if is_state_c:
                    # Low disaster history for State C
                    if dt in state_c_flood_dates and d.code == "DST-C1":
                        # Exactly 2 major flood events generated for State C
                        rain = round(float(self.rng.uniform(145.0, 175.0)), 2)
                        is_flood = True
                        flood_risk = "SEVERE"
                    elif dt in state_c_flood_dates and d.code == "DST-C2":
                        # Secondary district experiences moderate spillover
                        rain = round(float(self.rng.uniform(70.0, 95.0)), 2)
                        is_flood = False
                        flood_risk = "MODERATE"
                    else:
                        if is_monsoon:
                            rain = round(float(max(0.0, self.rng.exponential(8.5) if self.rng.uniform() < 0.40 else 0.0)), 2)
                        else:
                            rain = round(float(max(0.0, self.rng.exponential(1.5) if self.rng.uniform() < 0.08 else 0.0)), 2)
                        is_flood = False
                        flood_risk = "MODERATE" if rain > 45 else "LOW"
                else:
                    # States A and B (higher monsoon activity)
                    if is_monsoon:
                        # 60% chance of rain on monsoon days
                        if self.rng.uniform() < 0.58:
                            rain = round(float(self.rng.gamma(shape=2.5, scale=18.0)), 2)
                        else:
                            rain = 0.0
                    else:
                        # Non-monsoon dry season
                        rain = round(float(self.rng.exponential(2.0) if self.rng.uniform() < 0.07 else 0.0), 2)

                    # Major flood event definition: rainfall > 110 mm
                    is_flood = bool(rain >= 110.0 and is_monsoon)
                    if is_flood:
                        flood_risk = "SEVERE"
                    elif rain > 50.0:
                        flood_risk = "MODERATE"
                    else:
                        flood_risk = "LOW"

                records.append(
                    {
                        "district_code": d.code,
                        "state_code": d.state_code,
                        "record_date": dt.date(),
                        "rainfall_mm": rain,
                        "temperature_celsius": temp,
                        "flood_risk": flood_risk,
                        "is_major_flood_event": is_flood,
                    }
                )

        df = pd.DataFrame(records)
        return df

    # =========================================================================
    # Telemetry: Power & Outages
    # =========================================================================

    def _generate_power_telemetry(self, df_weather: pd.DataFrame) -> pd.DataFrame:
        records = []
        # Pre-index weather by (district_code, record_date)
        w_idx = df_weather.set_index(["district_code", "record_date"])

        for p in self.phcs:
            state = next(s for s in self.states if s.code == p.state_code)
            dates = pd.date_range(state.start_date, state.end_date, freq="D")

            for dt in dates:
                d_date = dt.date()
                w_row = w_idx.loc[(p.district_code, d_date)]
                rain = float(w_row["rainfall_mm"])
                flood_risk = str(w_row["flood_risk"])

                # Baseline outage hours (remote PHCs have poorer line reliability)
                base_outage = 1.8 if not p.remote_flag else 3.8
                
                # Storm / rain effect on grid line trips
                weather_penalty = 0.0
                if rain > 80.0 or flood_risk == "SEVERE":
                    weather_penalty = float(self.rng.uniform(7.0, 14.0))
                elif rain > 35.0 or flood_risk == "MODERATE":
                    weather_penalty = float(self.rng.uniform(2.5, 6.0))

                outage = min(24.0, max(0.0, float(base_outage + weather_penalty + self.rng.normal(0, 0.75))))
                outage = round(outage, 2)
                uptime = round(24.0 - outage, 2)

                # Generator fuel consumed: 2.2 L per outage hour when generator runs
                fuel_consumed = round(outage * 2.2 * (0.85 if p.solar_capacity_kw > 0 else 1.0), 2)

                records.append(
                    {
                        "phc_code": p.code,
                        "record_date": d_date,
                        "outage_hours": outage,
                        "grid_uptime_hours": uptime,
                        "generator_fuel_consumed_liters": fuel_consumed,
                    }
                )

        return pd.DataFrame(records)

    # =========================================================================
    # Telemetry: Patient Cases (OPD, Emergency, Diarrheal, Fever, Deliveries)
    # =========================================================================

    def _generate_patient_telemetry(self, df_weather: pd.DataFrame) -> pd.DataFrame:
        records = []
        w_idx = df_weather.set_index(["district_code", "record_date"])

        for p in self.phcs:
            state = next(s for s in self.states if s.code == p.state_code)
            dates = pd.date_range(state.start_date, state.end_date, freq="D")
            pop_k = p.catchment_population / 1000.0

            # Pre-fetch weather series for rainfall lag calculations
            rain_series = [w_idx.loc[(p.district_code, dt.date())]["rainfall_mm"] for dt in dates]

            for i, dt in enumerate(dates):
                d_date = dt.date()
                day_of_week = dt.dayofweek  # 0=Mon, 6=Sun
                
                # 1. Weekly Seasonality: Monday/Tuesday high, Sunday minimal OPD
                weekday_mult = {
                    0: 1.25, # Mon
                    1: 1.15, # Tue
                    2: 1.05, # Wed
                    3: 1.00, # Thu
                    4: 1.05, # Fri
                    5: 0.90, # Sat
                    6: 0.35, # Sun (OPD closed, only emergency)
                }[day_of_week]

                # 2. Rainfall Lag (2-3 days for diarrhea, 7-10 days for vector-borne fever)
                rain_lag_2d = rain_series[max(0, i - 2)]
                rain_lag_3d = rain_series[max(0, i - 3)]
                rain_lag_8d = rain_series[max(0, i - 8)] if i >= 8 else 0.0

                # 3. Diarrhoeal cases: surge 2-3 days after high rain
                diarrhea_base = pop_k * 0.18
                if rain_lag_2d > 40.0 or rain_lag_3d > 40.0:
                    diarrhea_mult = float(self.rng.uniform(2.2, 3.8))
                else:
                    diarrhea_mult = float(self.rng.uniform(0.8, 1.2))
                diarrheal_cases = int(max(0, round(diarrhea_base * diarrhea_mult + self.rng.normal(0, 1.0))))

                # 4. Fever cases: surge 7-10 days after pooling
                fever_base = pop_k * 0.35
                if rain_lag_8d > 35.0:
                    fever_mult = float(self.rng.uniform(1.8, 3.0))
                else:
                    fever_mult = float(self.rng.uniform(0.85, 1.25))
                fever_cases = int(max(0, round(fever_base * fever_mult + self.rng.normal(0, 1.5))))

                # 5. Deliveries: steady biological rate with Poisson distribution
                delivery_lambda = max(0.5, pop_k * 0.08)
                deliveries = int(self.rng.poisson(lam=delivery_lambda))

                # 6. Emergency cases: trauma, obstetric emergencies, acute illness
                emergency_base = pop_k * 0.12
                emergency_cases = int(max(0, round(self.rng.poisson(lam=emergency_base))))

                # 7. Total OPD cases: general primary care
                opd_base = pop_k * 2.8 * weekday_mult
                opd_cases = int(max(5, round(opd_base + diarrheal_cases * 0.6 + fever_cases * 0.8 + self.rng.normal(0, 3.0))))

                # 8. Realistic Outliers: Specific localized outbreak events
                # e.g., Water tank contamination outbreak at remote PHC-DST-A1-05 on 2024-08-20
                if p.code == "PHC-DST-A1-05" and d_date == date(2024, 8, 20):
                    diarrheal_cases = int(diarrheal_cases * 5.2)  # clear outlier
                    opd_cases += diarrheal_cases
                # Dengue cluster outbreak at PHC-DST-B1-02 on 2024-10-12
                if p.code == "PHC-DST-B1-02" and d_date == date(2024, 10, 12):
                    fever_cases = int(fever_cases * 4.5)  # clear outlier
                    opd_cases += fever_cases

                records.append(
                    {
                        "phc_code": p.code,
                        "record_date": d_date,
                        "opd_cases": opd_cases,
                        "emergency_cases": emergency_cases,
                        "diarrhoeal_cases": diarrheal_cases,
                        "fever_cases": fever_cases,
                        "deliveries": deliveries,
                    }
                )

        return pd.DataFrame(records)

    # =========================================================================
    # Telemetry: Workforce & Staff Absenteeism
    # =========================================================================

    def _generate_workforce_telemetry(self, df_weather: pd.DataFrame) -> pd.DataFrame:
        records = []
        w_idx = df_weather.set_index(["district_code", "record_date"])

        for p in self.phcs:
            state = next(s for s in self.states if s.code == p.state_code)
            dates = pd.date_range(state.start_date, state.end_date, freq="D")

            for dt in dates:
                d_date = dt.date()
                w_row = w_idx.loc[(p.district_code, d_date)]
                rain = float(w_row["rainfall_mm"])
                is_sunday = (dt.dayofweek == 6)

                # Baseline absenteeism: 4% to 7%
                absenteeism = float(self.rng.uniform(0.04, 0.08))

                # Sunday rotation
                if is_sunday:
                    absenteeism += 0.40

                # Severe flood blocks road access for staff traveling from towns
                if rain > 80.0 or w_row["flood_risk"] == "SEVERE":
                    absenteeism += float(self.rng.uniform(0.30, 0.55))

                absenteeism = min(0.85, round(absenteeism, 4))

                # On-duty counts (always ensure at least minimal coverage on weekdays)
                mo_duty = max(1 if not is_sunday else 0, round(p.staff_mo * (1.0 - absenteeism)))
                nurse_duty = max(1, round(p.staff_nurse * (1.0 - absenteeism)))
                anm_duty = max(1 if not is_sunday else 0, round(p.staff_anm * (1.0 - absenteeism)))

                records.append(
                    {
                        "phc_code": p.code,
                        "record_date": d_date,
                        "mo_on_duty": int(mo_duty),
                        "nurse_on_duty": int(nurse_duty),
                        "anm_on_duty": int(anm_duty),
                        "absenteeism_rate": absenteeism,
                    }
                )

        return pd.DataFrame(records)

    # =========================================================================
    # Telemetry: Bed Occupancy
    # =========================================================================

    def _generate_bed_telemetry(self, df_patient: pd.DataFrame) -> pd.DataFrame:
        records = []
        p_idx = df_patient.set_index(["phc_code", "record_date"])

        for p in self.phcs:
            state = next(s for s in self.states if s.code == p.state_code)
            dates = pd.date_range(state.start_date, state.end_date, freq="D")
            tot_beds = p.total_beds

            for dt in dates:
                d_date = dt.date()
                p_row = p_idx.loc[(p.code, d_date)]
                deliveries = int(p_row["deliveries"])
                emergencies = int(p_row["emergency_cases"])
                diarrhea = int(p_row["diarrhoeal_cases"])

                # Postnatal stay (1-2 days) + fraction of emergencies/dehydration admitted
                admissions = deliveries + int(round(emergencies * 0.4)) + int(round(diarrhea * 0.15))
                # Add previous day rollover
                occupied = min(tot_beds, max(0, int(round(admissions * self.rng.uniform(0.8, 1.2)))))
                available = max(0, tot_beds - occupied)

                records.append(
                    {
                        "phc_code": p.code,
                        "record_date": d_date,
                        "total_beds": tot_beds,
                        "occupied_beds": occupied,
                        "available_beds": available,
                    }
                )

        return pd.DataFrame(records)

    # =========================================================================
    # Telemetry: Pharmaceutical Inventory (Demand-Driven & No Negative Stock)
    # =========================================================================

    def _generate_inventory_telemetry(
        self, df_patient: pd.DataFrame, df_weather: pd.DataFrame
    ) -> pd.DataFrame:
        records = []
        p_idx = df_patient.set_index(["phc_code", "record_date"])
        w_idx = df_weather.set_index(["district_code", "record_date"])

        for p in self.phcs:
            state = next(s for s in self.states if s.code == p.state_code)
            dates = pd.date_range(state.start_date, state.end_date, freq="D")

            # Initialize stock for each medicine at this PHC
            current_stock: Dict[str, float] = {}
            for med in self.medicines:
                # 25-day initial buffer stock
                pop_k = p.catchment_population / 1000.0
                est_daily = pop_k * med.units_per_case * 2.0
                current_stock[med.id] = round(est_daily * 25.0, 2)

            # Track pending replenishment orders: list of (arrival_date, med_id, qty)
            pending_deliveries: List[Tuple[date, str, float]] = []

            for i, dt in enumerate(dates):
                d_date = dt.date()
                p_row = p_idx.loc[(p.code, d_date)]
                w_row = w_idx.loc[(p.district_code, d_date)]
                is_flood = bool(w_row["is_major_flood_event"])

                # Check if bi-weekly replenishment order is dispatched from warehouse (every 14 days)
                if i % 14 == 0:
                    # Replenishment lead time: 3 days baseline, +4 days if flood/blocked roads
                    lead_days = 3 if not is_flood else 7
                    arrival_dt = d_date + timedelta(days=lead_days)
                    for med in self.medicines:
                        # Order quantity to restore 30-day buffer
                        pop_k = p.catchment_population / 1000.0
                        order_qty = round(pop_k * med.units_per_case * 2.0 * 20.0, 2)
                        pending_deliveries.append((arrival_dt, med.id, order_qty))

                # Receive arrived deliveries for today
                received_today: Dict[str, float] = {m.id: 0.0 for m in self.medicines}
                remaining_deliveries = []
                for arr_date, med_id, qty in pending_deliveries:
                    if arr_date == d_date:
                        received_today[med_id] += qty
                    elif arr_date > d_date:
                        remaining_deliveries.append((arr_date, med_id, qty))
                pending_deliveries = remaining_deliveries

                # Compute daily consumption and inventory balance
                for med in self.medicines:
                    metric_val = float(p_row[med.driven_by_patient_metric])
                    # Demand strictly proportional to clinical caseload
                    demand = round(max(0.0, metric_val * med.units_per_case + self.rng.normal(0, 0.2)), 2)

                    opening = current_stock[med.id]
                    received = received_today[med.id]
                    available = opening + received

                    # Stockout prevention rule: consumption cannot exceed available stock
                    consumed = min(available, demand)
                    closing = max(0.0, round(available - consumed, 2))

                    # Update for next day
                    current_stock[med.id] = closing

                    records.append(
                        {
                            "phc_code": p.code,
                            "medicine_id": med.id,
                            "record_date": d_date,
                            "opening_stock": opening,
                            "received": received,
                            "consumed": consumed,
                            "closing_stock": closing,
                        }
                    )

        return pd.DataFrame(records)

    # =========================================================================
    # Telemetry: Road Logistics & Transit Times
    # =========================================================================

    def _generate_road_telemetry(self, df_weather: pd.DataFrame) -> pd.DataFrame:
        records = []
        w_idx = df_weather.set_index(["district_code", "record_date"])

        # Create road edges between adjacent PHCs within each district (chain topology)
        for d in self.districts:
            d_phcs = [p for p in self.phcs if p.district_code == d.code]
            state = next(s for s in self.states if s.code == d.state_code)
            dates = pd.date_range(state.start_date, state.end_date, freq="D")

            # Consecutive pairs (e.g. PHC1 <-> PHC2, PHC2 <-> PHC3, etc.)
            edges = []
            for k in range(len(d_phcs) - 1):
                edges.append((d_phcs[k], d_phcs[k + 1]))

            for origin, dest in edges:
                # Geometric distance
                dist_km = round(
                    float(
                        np.sqrt(
                            (origin.latitude - dest.latitude) ** 2
                            + (origin.longitude - dest.longitude) ** 2
                        )
                        * 111.0
                    ),
                    1,
                )
                dist_km = max(8.0, dist_km)
                base_transit_mins = round((dist_km / 40.0) * 60.0, 1)  # 40 km/h baseline

                for dt in dates:
                    d_date = dt.date()
                    w_row = w_idx.loc[(d.code, d_date)]
                    rain = float(w_row["rainfall_mm"])
                    flood_risk = str(w_row["flood_risk"])

                    if flood_risk == "SEVERE" or rain > 90.0:
                        # 65% chance road is completely blocked during severe flood
                        if self.rng.uniform() < 0.65:
                            status = "BLOCKED"
                            transit_mins = round(base_transit_mins * float(self.rng.uniform(4.5, 7.0)), 1)
                        else:
                            status = "DEGRADED"
                            transit_mins = round(base_transit_mins * float(self.rng.uniform(2.2, 3.5)), 1)
                    elif flood_risk == "MODERATE" or rain > 40.0:
                        status = "DEGRADED"
                        transit_mins = round(base_transit_mins * float(self.rng.uniform(1.4, 2.0)), 1)
                    else:
                        status = "OPEN"
                        transit_mins = round(base_transit_mins * float(self.rng.uniform(0.95, 1.10)), 1)

                    records.append(
                        {
                            "origin_phc_code": origin.code,
                            "destination_phc_code": dest.code,
                            "district_code": d.code,
                            "record_date": d_date,
                            "distance_km": dist_km,
                            "travel_time_minutes": transit_mins,
                            "road_status": status,
                            "flood_risk": flood_risk,
                        }
                    )

        return pd.DataFrame(records)

    # =========================================================================
    # Missing Values Injection
    # =========================================================================

    def _inject_missing_values(
        self, df: pd.DataFrame, columns: List[str], missing_rate: float
    ) -> pd.DataFrame:
        """Inject realistic None values into telemetry data at controlled rate."""
        df_copy = df.copy()
        n = len(df_copy)
        for col in columns:
            if col in df_copy.columns:
                mask = self.rng.uniform(0, 1, size=n) < missing_rate
                df_copy.loc[mask, col] = np.nan
        return df_copy

    # =========================================================================
    # Exporter: Save Parquet and CSV Snapshots
    # =========================================================================

    def export_snapshots(self, datasets: Dict[str, pd.DataFrame]) -> List[str]:
        """Export all generated tables to CSV and Parquet formats under data/raw/."""
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        exported_files = []

        for name, df in datasets.items():
            if name.endswith("_clean"):
                continue  # internal testing helper
            csv_path = RAW_DATA_DIR / f"{name}.csv"
            parquet_path = RAW_DATA_DIR / f"{name}.parquet"

            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path, index=False)

            exported_files.append(str(csv_path))
            exported_files.append(str(parquet_path))

        return exported_files
