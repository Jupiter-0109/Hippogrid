-- HippoGrid System of Record Initial Schema
-- Migration: 20260930000001_initial_schema.sql
-- Description: Core master tables, operational observability, digital twin forecasts,
--              resource optimization plans, stress test frontiers, and audit logs.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. Administrative Master Data
-- ============================================================================

CREATE TABLE IF NOT EXISTS states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_id UUID NOT NULL REFERENCES states(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    headquarters VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS phcs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    facility_type VARCHAR(50) NOT NULL DEFAULT 'PHC', -- PHC, CHC, Sub-centre
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    catchment_population INTEGER NOT NULL DEFAULT 30000,
    backup_power_type VARCHAR(50) DEFAULT 'DIESEL_GENERATOR',
    backup_power_capacity_kva NUMERIC(8, 2) DEFAULT 15.0,
    solar_capacity_kw NUMERIC(8, 2) DEFAULT 5.0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS warehouses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    cold_chain_capacity_liters NUMERIC(10, 2) DEFAULT 10000.0,
    dry_storage_capacity_sqm NUMERIC(10, 2) DEFAULT 500.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. Services, Dependencies & Medicines
-- ============================================================================

CREATE TABLE IF NOT EXISTS services (
    id VARCHAR(50) PRIMARY KEY, -- e.g. cold_chain_immunization, emergency_obstetric_care
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    criticality VARCHAR(20) NOT NULL DEFAULT 'CRITICAL', -- CRITICAL, HIGH, STANDARD
    min_staff_required INTEGER NOT NULL DEFAULT 1,
    requires_uninterrupted_power BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS service_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id VARCHAR(50) NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL, -- POWER, OXYGEN, WATER, STAFF, MEDICINE, COLD_CHAIN
    dependency_identifier VARCHAR(100) NOT NULL,
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    threshold_min_hours NUMERIC(6, 2) NOT NULL DEFAULT 12.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medicines (
    id VARCHAR(50) PRIMARY KEY, -- e.g. oxytocin_inj, magnesium_sulfate
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    is_cold_chain_required BOOLEAN NOT NULL DEFAULT FALSE,
    min_temp_celsius NUMERIC(4, 1),
    max_temp_celsius NUMERIC(4, 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 3. Operational Observability & Telemetry
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    medicine_id VARCHAR(50) NOT NULL REFERENCES medicines(id),
    quantity_change NUMERIC(10, 2) NOT NULL,
    stock_after NUMERIC(10, 2) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL, -- INBOUND, DISPENSED, EXPIRED, TRANSFER
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patient_visits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id),
    visit_count INTEGER NOT NULL DEFAULT 1,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bed_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    total_beds INTEGER NOT NULL DEFAULT 6,
    occupied_beds INTEGER NOT NULL DEFAULT 0,
    critical_care_beds INTEGER NOT NULL DEFAULT 0,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workforce_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    medical_officers_on_duty INTEGER NOT NULL DEFAULT 1,
    staff_nurses_on_duty INTEGER NOT NULL DEFAULT 2,
    lab_technicians_on_duty INTEGER NOT NULL DEFAULT 1,
    pharmacists_on_duty INTEGER NOT NULL DEFAULT 1,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS power_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    grid_available BOOLEAN NOT NULL DEFAULT TRUE,
    generator_fuel_liters NUMERIC(8, 2) NOT NULL DEFAULT 100.0,
    battery_charge_percent NUMERIC(5, 2) NOT NULL DEFAULT 100.0,
    cold_chain_temp_celsius NUMERIC(5, 2) NOT NULL DEFAULT 4.0,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    temperature_celsius NUMERIC(5, 2),
    rainfall_mm_per_hour NUMERIC(6, 2) NOT NULL DEFAULT 0.0,
    flood_risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW', -- LOW, MODERATE, SEVERE
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS road_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    destination_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    distance_km NUMERIC(6, 2) NOT NULL,
    transit_duration_minutes NUMERIC(6, 1) NOT NULL,
    passability_status VARCHAR(20) NOT NULL DEFAULT 'PASSABLE', -- PASSABLE, DEGRADED, BLOCKED
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. Twin Forecasts & Service Continuity
-- ============================================================================

CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id),
    target_metric VARCHAR(50) NOT NULL, -- e.g. stock_level, fuel_level, demand
    forecast_horizon_hours INTEGER NOT NULL,
    predicted_value NUMERIC(10, 2) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conformal_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id UUID NOT NULL REFERENCES forecasts(id) ON DELETE CASCADE,
    confidence_level NUMERIC(4, 2) NOT NULL DEFAULT 0.95,
    lower_bound NUMERIC(10, 2) NOT NULL,
    upper_bound NUMERIC(10, 2) NOT NULL,
    nonconformity_score NUMERIC(10, 4)
);

CREATE TABLE IF NOT EXISTS service_continuity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id),
    status VARCHAR(20) NOT NULL DEFAULT 'HEALTHY', -- HEALTHY, WARNING, CRITICAL, COMPROMISED
    hours_to_compromise NUMERIC(6, 1) NOT NULL,
    primary_bottleneck VARCHAR(100) NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    description TEXT,
    shock_type VARCHAR(50) NOT NULL, -- POWER_OUTAGE, FLASH_FLOOD, SURGE_DEMAND, COMPOUND
    severity_level VARCHAR(20) NOT NULL DEFAULT 'HIGH',
    parameters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenario_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id),
    service_failure_hour NUMERIC(6, 1),
    is_compromised BOOLEAN NOT NULL DEFAULT FALSE,
    details_json JSONB DEFAULT '{}'::jsonb,
    simulated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 5. Optimization & Resource Interventions
-- ============================================================================

CREATE TABLE IF NOT EXISTS resource_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED', -- PROPOSED, APPROVED, MODIFIED, REJECTED, EXECUTED
    total_cost NUMERIC(12, 2) DEFAULT 0.0,
    services_saved INTEGER DEFAULT 0,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plan_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES resource_plans(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- MEDICINE, FUEL, STAFF, OXYGEN
    resource_identifier VARCHAR(100) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    source_type VARCHAR(30) NOT NULL, -- WAREHOUSE, PHC
    source_id UUID NOT NULL,
    target_phc_id UUID NOT NULL REFERENCES phcs(id),
    scheduled_departure TIMESTAMPTZ,
    estimated_arrival TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS plan_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES resource_plans(id) ON DELETE CASCADE,
    actor_id VARCHAR(100) NOT NULL,
    actor_role VARCHAR(50) NOT NULL, -- DISTRICT_HEALTH_OFFICER, PHC_CHIEF
    action VARCHAR(30) NOT NULL, -- APPROVED, MODIFIED, REJECTED
    override_reason TEXT,
    modified_transfers_json JSONB,
    feedback_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 6. Stress Testing, Federated Models & Governance
-- ============================================================================

CREATE TABLE IF NOT EXISTS stress_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    run_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    shocks_combined VARCHAR(150) NOT NULL,
    system_breakdown_threshold NUMERIC(5, 2)
);

CREATE TABLE IF NOT EXISTS stress_frontiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stress_test_id UUID NOT NULL REFERENCES stress_tests(id) ON DELETE CASCADE,
    shock_intensity_x NUMERIC(6, 2) NOT NULL,
    shock_intensity_y NUMERIC(6, 2) NOT NULL,
    network_survival_rate NUMERIC(5, 2) NOT NULL,
    critical_cutset_json JSONB
);

CREATE TABLE IF NOT EXISTS federated_models (
    id VARCHAR(50) PRIMARY KEY, -- e.g. continuity_cox_v1, shock_propagation_gnn
    name VARCHAR(150) NOT NULL,
    version VARCHAR(30) NOT NULL,
    aggregation_round INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(50) NOT NULL REFERENCES federated_models(id) ON DELETE CASCADE,
    district_id UUID NOT NULL REFERENCES districts(id),
    sample_size INTEGER NOT NULL,
    metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    user_id VARCHAR(100),
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_phcs_district ON phcs(district_id);
CREATE INDEX IF NOT EXISTS idx_service_continuity_phc ON service_continuity(phc_id);
CREATE INDEX IF NOT EXISTS idx_service_continuity_status ON service_continuity(status);
CREATE INDEX IF NOT EXISTS idx_inventory_phc_med ON inventory_transactions(phc_id, medicine_id);
CREATE INDEX IF NOT EXISTS idx_plan_transfers_plan ON plan_transfers(plan_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event ON audit_logs(event_type, created_at);
