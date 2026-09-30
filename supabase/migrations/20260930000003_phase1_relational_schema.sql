-- HippoGrid Phase 1 Relational Database Schema & Views
-- Migration: 20260930000003_phase1_relational_schema.sql
-- Description: Complete 27-table relational schema, constraints, indexes, and analytical views.

-- 1. Service Dependencies
CREATE TABLE IF NOT EXISTS service_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id VARCHAR(50) NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL,
    dependency_identifier VARCHAR(100) NOT NULL,
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    threshold_min_hours NUMERIC(6, 2) NOT NULL DEFAULT 12.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Operational Telemetry Tables
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    medicine_id VARCHAR(50) NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    quantity_change NUMERIC(10, 2) NOT NULL,
    stock_after NUMERIC(10, 2) NOT NULL CHECK (stock_after >= 0),
    transaction_type VARCHAR(30) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patient_visits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    visit_count INTEGER NOT NULL DEFAULT 1 CHECK (visit_count >= 0),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bed_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    total_beds INTEGER NOT NULL CHECK (total_beds >= 0),
    occupied_beds INTEGER NOT NULL CHECK (occupied_beds >= 0),
    critical_care_beds INTEGER NOT NULL DEFAULT 0 CHECK (critical_care_beds >= 0),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workforce_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    medical_officers_on_duty INTEGER NOT NULL DEFAULT 1 CHECK (medical_officers_on_duty >= 0),
    staff_nurses_on_duty INTEGER NOT NULL DEFAULT 2 CHECK (staff_nurses_on_duty >= 0),
    anm_on_duty INTEGER NOT NULL DEFAULT 2 CHECK (anm_on_duty >= 0),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS power_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    grid_available BOOLEAN NOT NULL DEFAULT TRUE,
    outage_hours NUMERIC(5, 2) DEFAULT 0.0 CHECK (outage_hours >= 0 AND outage_hours <= 24),
    generator_fuel_liters NUMERIC(8, 2) NOT NULL DEFAULT 100.0 CHECK (generator_fuel_liters >= 0),
    battery_charge_percent NUMERIC(5, 2) NOT NULL DEFAULT 100.0 CHECK (battery_charge_percent >= 0 AND battery_charge_percent <= 100),
    cold_chain_temp_celsius NUMERIC(5, 2) NOT NULL DEFAULT 4.0,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    temperature_celsius NUMERIC(5, 2),
    rainfall_mm_per_hour NUMERIC(6, 2) NOT NULL DEFAULT 0.0 CHECK (rainfall_mm_per_hour >= 0),
    flood_risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS road_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    destination_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    distance_km NUMERIC(6, 2) NOT NULL CHECK (distance_km > 0),
    transit_duration_minutes NUMERIC(6, 1) NOT NULL CHECK (transit_duration_minutes >= 0),
    passability_status VARCHAR(20) NOT NULL DEFAULT 'PASSABLE',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Forecasting, Conformal Bounds & Continuity
CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    target_metric VARCHAR(50) NOT NULL,
    forecast_horizon_hours INTEGER NOT NULL CHECK (forecast_horizon_hours > 0),
    predicted_value NUMERIC(10, 2) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conformal_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id UUID NOT NULL REFERENCES forecasts(id) ON DELETE CASCADE,
    confidence_level NUMERIC(4, 2) NOT NULL DEFAULT 0.95,
    lower_bound NUMERIC(10, 2) NOT NULL,
    upper_bound NUMERIC(10, 2) NOT NULL,
    nonconformity_score NUMERIC(10, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS service_continuity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'HEALTHY',
    hours_to_compromise NUMERIC(6, 1) NOT NULL,
    primary_bottleneck VARCHAR(100) NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Scenarios & Results
CREATE TABLE IF NOT EXISTS scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    description TEXT,
    shock_type VARCHAR(50) NOT NULL,
    severity_level VARCHAR(20) NOT NULL DEFAULT 'HIGH',
    parameters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenario_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    service_id VARCHAR(50) NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    service_failure_hour NUMERIC(6, 1),
    is_compromised BOOLEAN NOT NULL DEFAULT FALSE,
    details_json JSONB DEFAULT '{}'::jsonb,
    simulated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Resource Optimization Plans & Transfers
CREATE TABLE IF NOT EXISTS resource_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED',
    total_cost NUMERIC(12, 2) DEFAULT 0.0,
    services_saved INTEGER DEFAULT 0,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plan_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES resource_plans(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_identifier VARCHAR(100) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL CHECK (quantity > 0),
    source_type VARCHAR(30) NOT NULL,
    source_id UUID NOT NULL,
    target_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    scheduled_departure TIMESTAMPTZ,
    estimated_arrival TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plan_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES resource_plans(id) ON DELETE CASCADE,
    actor_id VARCHAR(100) NOT NULL,
    actor_role VARCHAR(50) NOT NULL,
    action VARCHAR(30) NOT NULL,
    override_reason TEXT,
    modified_transfers_json JSONB,
    feedback_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Stress Testing & Frontiers
CREATE TABLE IF NOT EXISTS stress_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    run_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    shocks_combined VARCHAR(150) NOT NULL,
    system_breakdown_threshold NUMERIC(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stress_frontiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stress_test_id UUID NOT NULL REFERENCES stress_tests(id) ON DELETE CASCADE,
    shock_intensity_x NUMERIC(6, 2) NOT NULL,
    shock_intensity_y NUMERIC(6, 2) NOT NULL,
    network_survival_rate NUMERIC(5, 2) NOT NULL,
    critical_cutset_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Federated Learning & Governance
CREATE TABLE IF NOT EXISTS federated_models (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    version VARCHAR(30) NOT NULL,
    aggregation_round INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(50) NOT NULL REFERENCES federated_models(id) ON DELETE CASCADE,
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    sample_size INTEGER NOT NULL,
    metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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

-- 8. Relational Indexes
CREATE INDEX IF NOT EXISTS idx_districts_state_id ON districts(state_id);
CREATE INDEX IF NOT EXISTS idx_phcs_district_id ON phcs(district_id);
CREATE INDEX IF NOT EXISTS idx_warehouses_district_id ON warehouses(district_id);
CREATE INDEX IF NOT EXISTS idx_service_deps_service_id ON service_dependencies(service_id);
CREATE INDEX IF NOT EXISTS idx_inv_tx_phc_id ON inventory_transactions(phc_id);
CREATE INDEX IF NOT EXISTS idx_inv_tx_med_id ON inventory_transactions(medicine_id);
CREATE INDEX IF NOT EXISTS idx_inv_tx_rec_at ON inventory_transactions(recorded_at);
CREATE INDEX IF NOT EXISTS idx_patient_visits_phc_id ON patient_visits(phc_id);
CREATE INDEX IF NOT EXISTS idx_patient_visits_svc_id ON patient_visits(service_id);
CREATE INDEX IF NOT EXISTS idx_patient_visits_rec_at ON patient_visits(recorded_at);
CREATE INDEX IF NOT EXISTS idx_bed_status_phc_id ON bed_status(phc_id);
CREATE INDEX IF NOT EXISTS idx_workforce_phc_id ON workforce_status(phc_id);
CREATE INDEX IF NOT EXISTS idx_power_status_phc_id ON power_status(phc_id);
CREATE INDEX IF NOT EXISTS idx_weather_district_id ON weather_observations(district_id);
CREATE INDEX IF NOT EXISTS idx_road_status_origin ON road_status(origin_phc_id);
CREATE INDEX IF NOT EXISTS idx_road_status_dest ON road_status(destination_phc_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_phc_id ON forecasts(phc_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_svc_id ON forecasts(service_id);
CREATE INDEX IF NOT EXISTS idx_continuity_phc_id ON service_continuity(phc_id);
CREATE INDEX IF NOT EXISTS idx_continuity_svc_id ON service_continuity(service_id);
CREATE INDEX IF NOT EXISTS idx_continuity_status ON service_continuity(status);
CREATE INDEX IF NOT EXISTS idx_continuity_assessed ON service_continuity(assessed_at);
CREATE INDEX IF NOT EXISTS idx_res_plans_dist_id ON resource_plans(district_id);
CREATE INDEX IF NOT EXISTS idx_plan_transfers_plan ON plan_transfers(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_transfers_target ON plan_transfers(target_phc_id);
CREATE INDEX IF NOT EXISTS idx_model_runs_dist ON model_runs(district_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event ON audit_logs(event_type, created_at);

-- 9. Analytical Views for Dashboard Queries
CREATE OR REPLACE VIEW v_phc_continuity_summary AS
SELECT 
    p.id AS phc_id,
    p.code AS phc_code,
    p.name AS phc_name,
    p.catchment_population,
    p.remote_flag,
    p.vulnerability_score,
    p.total_beds,
    d.id AS district_id,
    d.name AS district_name,
    s.id AS state_id,
    s.name AS state_name,
    COALESCE(sc.status, 'HEALTHY') AS overall_continuity_status,
    COALESCE(sc.hours_to_compromise, 72.0) AS min_hours_to_compromise,
    COALESCE(sc.primary_bottleneck, 'Nominal') AS primary_bottleneck,
    sc.service_id AS critical_service_id,
    pw.grid_available,
    pw.battery_charge_percent,
    pw.generator_fuel_liters
FROM phcs p
JOIN districts d ON d.id = p.district_id
JOIN states s ON s.id = d.state_id
LEFT JOIN LATERAL (
    SELECT status, hours_to_compromise, primary_bottleneck, service_id
    FROM service_continuity
    WHERE phc_id = p.id
    ORDER BY hours_to_compromise ASC, assessed_at DESC
    LIMIT 1
) sc ON TRUE
LEFT JOIN LATERAL (
    SELECT grid_available, battery_charge_percent, generator_fuel_liters
    FROM power_status
    WHERE phc_id = p.id
    ORDER BY recorded_at DESC
    LIMIT 1
) pw ON TRUE;

CREATE OR REPLACE VIEW v_service_risk_monitor AS
SELECT 
    svc.id AS service_id,
    svc.name AS service_name,
    svc.criticality,
    COUNT(p.id) AS total_phcs,
    COUNT(CASE WHEN sc.status IN ('CRITICAL', 'COMPROMISED') THEN 1 END) AS phcs_at_risk,
    ROUND(
        (1.0 - (COUNT(CASE WHEN sc.status IN ('CRITICAL', 'COMPROMISED') THEN 1 END)::NUMERIC / NULLIF(COUNT(p.id), 0))) * 100.0,
        1
    ) AS service_continuity_rate
FROM services svc
CROSS JOIN phcs p
LEFT JOIN LATERAL (
    SELECT status
    FROM service_continuity
    WHERE phc_id = p.id AND service_id = svc.id
    ORDER BY assessed_at DESC
    LIMIT 1
) sc ON TRUE
GROUP BY svc.id, svc.name, svc.criticality;

CREATE OR REPLACE VIEW v_daily_operational_snapshot AS
SELECT 
    p.id AS phc_id,
    p.code AS phc_code,
    p.name AS phc_name,
    d.name AS district_name,
    COALESCE(bs.occupied_beds, 0) AS occupied_beds,
    p.total_beds,
    COALESCE(ws.medical_officers_on_duty, 0) AS mo_on_duty,
    COALESCE(ws.staff_nurses_on_duty, 0) AS nurses_on_duty,
    COALESCE(pw.grid_available, TRUE) AS grid_available,
    COALESCE(pw.outage_hours, 0.0) AS outage_hours
FROM phcs p
JOIN districts d ON d.id = p.district_id
LEFT JOIN LATERAL (
    SELECT occupied_beds FROM bed_status WHERE phc_id = p.id ORDER BY recorded_at DESC LIMIT 1
) bs ON TRUE
LEFT JOIN LATERAL (
    SELECT medical_officers_on_duty, staff_nurses_on_duty FROM workforce_status WHERE phc_id = p.id ORDER BY recorded_at DESC LIMIT 1
) ws ON TRUE
LEFT JOIN LATERAL (
    SELECT grid_available, outage_hours FROM power_status WHERE phc_id = p.id ORDER BY recorded_at DESC LIMIT 1
) pw ON TRUE;
