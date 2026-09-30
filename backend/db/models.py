"""SQLAlchemy Declarative Models for HippoGrid System of Record.
Healthcare Infrastructure & Primary-care Planning Optimization Grid
"""
import uuid
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from backend.db.session import Base


# =============================================================================
# 1. Master & Administrative Models
# =============================================================================

class State(Base):
    __tablename__ = "states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    districts = relationship("District", back_populates="state", cascade="all, delete-orphan")


class District(Base):
    __tablename__ = "districts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    headquarters = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    state = relationship("State", back_populates="districts")
    phcs = relationship("PHC", back_populates="district", cascade="all, delete-orphan")
    warehouses = relationship("Warehouse", back_populates="district", cascade="all, delete-orphan")


class PHC(Base):
    __tablename__ = "phcs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    facility_type = Column(String(50), nullable=False, default="PHC")
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    catchment_population = Column(Integer, nullable=False, default=30000)
    remote_flag = Column(Boolean, nullable=False, default=False)
    vulnerability_score = Column(Numeric(5, 2), nullable=False, default=1.0)
    total_beds = Column(Integer, nullable=False, default=6)
    staff_mo = Column(Integer, nullable=False, default=1)
    staff_nurse = Column(Integer, nullable=False, default=2)
    staff_anm = Column(Integer, nullable=False, default=2)
    backup_power_type = Column(String(50), default="DIESEL_GENERATOR")
    backup_power_capacity_kva = Column(Numeric(8, 2), default=15.0)
    backup_power_hours = Column(Numeric(6, 2), default=24.0)
    solar_capacity_kw = Column(Numeric(8, 2), default=5.0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    district = relationship("District", back_populates="phcs")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    cold_chain_capacity_liters = Column(Numeric(10, 2), default=10000.0)
    dry_storage_capacity_sqm = Column(Numeric(10, 2), default=500.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    district = relationship("District", back_populates="warehouses")


class Service(Base):
    __tablename__ = "services"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    criticality = Column(String(20), nullable=False, default="CRITICAL")
    min_staff_required = Column(Integer, nullable=False, default=1)
    requires_uninterrupted_power = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dependencies = relationship("ServiceDependency", back_populates="service", cascade="all, delete-orphan")


class ServiceDependency(Base):
    __tablename__ = "service_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(String(50), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(String(50), nullable=False)
    dependency_identifier = Column(String(100), nullable=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    threshold_min_hours = Column(Numeric(6, 2), nullable=False, default=12.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    service = relationship("Service", back_populates="dependencies")


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    is_cold_chain_required = Column(Boolean, nullable=False, default=False)
    min_temp_celsius = Column(Numeric(4, 1), nullable=True)
    max_temp_celsius = Column(Numeric(4, 1), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# =============================================================================
# 2. Operational Observability & Telemetry Models
# =============================================================================

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint("stock_after >= 0", name="chk_stock_after_non_negative"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(String(50), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_change = Column(Numeric(10, 2), nullable=False)
    stock_after = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(String(30), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PatientVisit(Base):
    __tablename__ = "patient_visits"
    __table_args__ = (
        CheckConstraint("visit_count >= 0", name="chk_visit_count_non_negative"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(50), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_count = Column(Integer, nullable=False, default=1)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BedStatus(Base):
    __tablename__ = "bed_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    total_beds = Column(Integer, nullable=False, default=6)
    occupied_beds = Column(Integer, nullable=False, default=0)
    critical_care_beds = Column(Integer, nullable=False, default=0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WorkforceStatus(Base):
    __tablename__ = "workforce_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    medical_officers_on_duty = Column(Integer, nullable=False, default=1)
    staff_nurses_on_duty = Column(Integer, nullable=False, default=2)
    anm_on_duty = Column(Integer, nullable=False, default=2)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PowerStatus(Base):
    __tablename__ = "power_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    grid_available = Column(Boolean, nullable=False, default=True)
    outage_hours = Column(Numeric(5, 2), default=0.0)
    generator_fuel_liters = Column(Numeric(8, 2), nullable=False, default=100.0)
    battery_charge_percent = Column(Numeric(5, 2), nullable=False, default=100.0)
    cold_chain_temp_celsius = Column(Numeric(5, 2), nullable=False, default=4.0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    temperature_celsius = Column(Numeric(5, 2), nullable=True)
    rainfall_mm_per_hour = Column(Numeric(6, 2), nullable=False, default=0.0)
    flood_risk_level = Column(String(20), nullable=False, default="LOW")
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RoadStatus(Base):
    __tablename__ = "road_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    distance_km = Column(Numeric(6, 2), nullable=False)
    transit_duration_minutes = Column(Numeric(6, 1), nullable=False)
    passability_status = Column(String(20), nullable=False, default="PASSABLE")
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# =============================================================================
# 3. Forecasts, Conformal Prediction & Continuity
# =============================================================================

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(50), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    target_metric = Column(String(50), nullable=False)
    forecast_horizon_hours = Column(Integer, nullable=False)
    predicted_value = Column(Numeric(10, 2), nullable=False)
    model_version = Column(String(50), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conformal_bounds = relationship("ConformalPrediction", back_populates="forecast", cascade="all, delete-orphan")


class ConformalPrediction(Base):
    __tablename__ = "conformal_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(UUID(as_uuid=True), ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence_level = Column(Numeric(4, 2), nullable=False, default=0.95)
    lower_bound = Column(Numeric(10, 2), nullable=False)
    upper_bound = Column(Numeric(10, 2), nullable=False)
    nonconformity_score = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    forecast = relationship("Forecast", back_populates="conformal_bounds")


class ServiceContinuity(Base):
    __tablename__ = "service_continuity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(50), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="HEALTHY", index=True)
    hours_to_compromise = Column(Numeric(6, 1), nullable=False)
    primary_bottleneck = Column(String(100), nullable=False)
    assessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# =============================================================================
# 4. Scenarios & Results
# =============================================================================

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    shock_type = Column(String(50), nullable=False)
    severity_level = Column(String(20), nullable=False, default="HIGH")
    parameters_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    results = relationship("ScenarioResult", back_populates="scenario", cascade="all, delete-orphan")


class ScenarioResult(Base):
    __tablename__ = "scenario_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(50), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    service_failure_hour = Column(Numeric(6, 1), nullable=True)
    is_compromised = Column(Boolean, nullable=False, default=False)
    details_json = Column(JSONB, default=dict)
    simulated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    scenario = relationship("Scenario", back_populates="results")


# =============================================================================
# 5. Resource Optimization Plans & Feedback
# =============================================================================

class ResourcePlan(Base):
    __tablename__ = "resource_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="PROPOSED")
    total_cost = Column(Numeric(12, 2), default=0.0)
    services_saved = Column(Integer, default=0)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    transfers = relationship("PlanTransfer", back_populates="plan", cascade="all, delete-orphan")
    feedback = relationship("PlanFeedback", back_populates="plan", cascade="all, delete-orphan")


class PlanTransfer(Base):
    __tablename__ = "plan_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("resource_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_identifier = Column(String(100), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    source_type = Column(String(30), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    target_phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_departure = Column(DateTime(timezone=True), nullable=True)
    estimated_arrival = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plan = relationship("ResourcePlan", back_populates="transfers")


class PlanFeedback(Base):
    __tablename__ = "plan_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("resource_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(30), nullable=False)
    override_reason = Column(Text, nullable=True)
    modified_transfers_json = Column(JSONB, nullable=True)
    feedback_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plan = relationship("ResourcePlan", back_populates="feedback")


# =============================================================================
# 6. Stress Tests & Frontiers
# =============================================================================

class StressTest(Base):
    __tablename__ = "stress_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    run_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    shocks_combined = Column(String(150), nullable=False)
    system_breakdown_threshold = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    frontiers = relationship("StressFrontier", back_populates="stress_test", cascade="all, delete-orphan")


class StressFrontier(Base):
    __tablename__ = "stress_frontiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stress_test_id = Column(UUID(as_uuid=True), ForeignKey("stress_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    shock_intensity_x = Column(Numeric(6, 2), nullable=False)
    shock_intensity_y = Column(Numeric(6, 2), nullable=False)
    network_survival_rate = Column(Numeric(5, 2), nullable=False)
    critical_cutset_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    stress_test = relationship("StressTest", back_populates="frontiers")


# =============================================================================
# 7. Federated Learning Models & Governance
# =============================================================================

class FederatedModel(Base):
    __tablename__ = "federated_models"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    version = Column(String(30), nullable=False)
    aggregation_round = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    model_runs = relationship("ModelRun", back_populates="model", cascade="all, delete-orphan")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(50), ForeignKey("federated_models.id", ondelete="CASCADE"), nullable=False, index=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    sample_size = Column(Integer, nullable=False)
    metrics_json = Column(JSONB, nullable=False, default=dict)
    trained_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    model = relationship("FederatedModel", back_populates="model_runs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    details_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


# =============================================================================
# 8. Daily Telemetry Models (Phase 2 Compatible)
# =============================================================================

class DailyPatientRecord(Base):
    __tablename__ = "daily_patient_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    opd_cases = Column(Integer, nullable=True)
    emergency_cases = Column(Integer, nullable=True)
    diarrhoeal_cases = Column(Integer, nullable=True)
    fever_cases = Column(Integer, nullable=True)
    deliveries = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyInventoryRecord(Base):
    __tablename__ = "daily_inventory_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(String(50), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    opening_stock = Column(Numeric(10, 2), nullable=True)
    received = Column(Numeric(10, 2), nullable=False, default=0.0)
    consumed = Column(Numeric(10, 2), nullable=True)
    closing_stock = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyWorkforceRecord(Base):
    __tablename__ = "daily_workforce_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    mo_on_duty = Column(Integer, nullable=True)
    nurse_on_duty = Column(Integer, nullable=True)
    anm_on_duty = Column(Integer, nullable=True)
    absenteeism_rate = Column(Numeric(5, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyBedRecord(Base):
    __tablename__ = "daily_bed_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    total_beds = Column(Integer, nullable=False)
    occupied_beds = Column(Integer, nullable=True)
    available_beds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyPowerRecord(Base):
    __tablename__ = "daily_power_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    outage_hours = Column(Numeric(5, 2), nullable=True)
    grid_uptime_hours = Column(Numeric(5, 2), nullable=True)
    generator_fuel_consumed_liters = Column(Numeric(8, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyWeatherRecord(Base):
    __tablename__ = "daily_weather_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    rainfall_mm = Column(Numeric(7, 2), nullable=True)
    temperature_celsius = Column(Numeric(5, 2), nullable=True)
    flood_risk = Column(String(20), nullable=False, default="LOW")
    is_major_flood_event = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyRoadRecord(Base):
    __tablename__ = "daily_road_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_phc_id = Column(UUID(as_uuid=True), ForeignKey("phcs.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    travel_time_minutes = Column(Numeric(6, 1), nullable=True)
    road_status = Column(String(20), nullable=False, default="OPEN")
    flood_risk = Column(String(20), nullable=False, default="LOW")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
