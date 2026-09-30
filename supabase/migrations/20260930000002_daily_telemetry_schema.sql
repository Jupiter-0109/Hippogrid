-- HippoGrid Daily Telemetry Schema
-- Migration: 20260930000002_daily_telemetry_schema.sql
-- Description: Daily patient, inventory, workforce, bed, power, weather, and road telemetry.

CREATE TABLE IF NOT EXISTS daily_patient_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    opd_cases INTEGER,
    emergency_cases INTEGER,
    diarrhoeal_cases INTEGER,
    fever_cases INTEGER,
    deliveries INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_patient_phc_date UNIQUE (phc_id, record_date)
);

CREATE TABLE IF NOT EXISTS daily_inventory_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    medicine_id VARCHAR(50) NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    opening_stock NUMERIC(10, 2),
    received NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    consumed NUMERIC(10, 2),
    closing_stock NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inv_phc_med_date UNIQUE (phc_id, medicine_id, record_date)
);

CREATE TABLE IF NOT EXISTS daily_workforce_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    mo_on_duty INTEGER,
    nurse_on_duty INTEGER,
    anm_on_duty INTEGER,
    absenteeism_rate NUMERIC(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_workforce_phc_date UNIQUE (phc_id, record_date)
);

CREATE TABLE IF NOT EXISTS daily_bed_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    total_beds INTEGER NOT NULL,
    occupied_beds INTEGER,
    available_beds INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_bed_phc_date UNIQUE (phc_id, record_date)
);

CREATE TABLE IF NOT EXISTS daily_power_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    outage_hours NUMERIC(5, 2),
    grid_uptime_hours NUMERIC(5, 2),
    generator_fuel_consumed_liters NUMERIC(8, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_power_phc_date UNIQUE (phc_id, record_date)
);

CREATE TABLE IF NOT EXISTS daily_weather_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    rainfall_mm NUMERIC(7, 2),
    temperature_celsius NUMERIC(5, 2),
    flood_risk VARCHAR(20) NOT NULL DEFAULT 'LOW',
    is_major_flood_event BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_weather_dist_date UNIQUE (district_id, record_date)
);

CREATE TABLE IF NOT EXISTS daily_road_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    destination_phc_id UUID NOT NULL REFERENCES phcs(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    travel_time_minutes NUMERIC(6, 1),
    road_status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    flood_risk VARCHAR(20) NOT NULL DEFAULT 'LOW',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_road_phcs_date UNIQUE (origin_phc_id, destination_phc_id, record_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_patient_date ON daily_patient_records(record_date);
CREATE INDEX IF NOT EXISTS idx_daily_inv_date ON daily_inventory_records(record_date);
CREATE INDEX IF NOT EXISTS idx_daily_workforce_date ON daily_workforce_records(record_date);
CREATE INDEX IF NOT EXISTS idx_daily_weather_date ON daily_weather_records(record_date);
