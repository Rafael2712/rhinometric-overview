-- AI Anomaly Engine V1 — Isolated tables
-- Safe to create: no FK to existing tables, _v1 suffix, no collisions

CREATE TABLE IF NOT EXISTS anomaly_engine_results_v1 (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint     VARCHAR(64) NOT NULL,
    service_id      INTEGER NOT NULL,
    service_name    VARCHAR(255) NOT NULL,
    anomaly_score   SMALLINT NOT NULL CHECK (anomaly_score BETWEEN 0 AND 100),
    severity        VARCHAR(20) NOT NULL,
    confidence      REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    confidence_label VARCHAR(20) NOT NULL,
    primary_category VARCHAR(30) NOT NULL,
    category_scores JSONB NOT NULL,
    reason_codes    JSONB NOT NULL,
    evidence_summary TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    first_seen_at   TIMESTAMPTZ NOT NULL,
    last_seen_at    TIMESTAMPTZ NOT NULL,
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    environment     VARCHAR(100),
    group_name      VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aev1_fingerprint ON anomaly_engine_results_v1(fingerprint);
CREATE INDEX IF NOT EXISTS idx_aev1_service_id ON anomaly_engine_results_v1(service_id);
CREATE INDEX IF NOT EXISTS idx_aev1_severity_status ON anomaly_engine_results_v1(severity, status);
CREATE INDEX IF NOT EXISTS idx_aev1_status_lastseen ON anomaly_engine_results_v1(status, last_seen_at);

CREATE TABLE IF NOT EXISTS anomaly_engine_history_v1 (
    id              BIGSERIAL PRIMARY KEY,
    service_id      INTEGER NOT NULL,
    service_name    VARCHAR(255) NOT NULL,
    anomaly_score   SMALLINT NOT NULL,
    severity        VARCHAR(20) NOT NULL,
    category_scores JSONB NOT NULL,
    reason_codes_summary VARCHAR(500),
    snapshot_data   JSONB,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aehv1_svc_time ON anomaly_engine_history_v1(service_id, recorded_at);
