-- HippoGrid Data Quality Results Schema
-- Migration: 20260930000004_data_quality_results.sql
-- Description: Audit and scoring table for telemetry data quality runs.

CREATE TABLE IF NOT EXISTS data_quality_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(50) NOT NULL,
    dataset VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rows_checked INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    warnings INTEGER NOT NULL DEFAULT 0,
    quality_score NUMERIC(5, 2) NOT NULL DEFAULT 100.0,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dq_run_id ON data_quality_results(run_id);
CREATE INDEX IF NOT EXISTS idx_dq_dataset ON data_quality_results(dataset);
CREATE INDEX IF NOT EXISTS idx_dq_timestamp ON data_quality_results(timestamp);
