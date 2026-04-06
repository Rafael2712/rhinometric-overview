-- Phase V1.1: Add validation fields to anomaly_engine_results_v1
ALTER TABLE anomaly_engine_results_v1 ADD COLUMN IF NOT EXISTS baseline_deviation_pct real;
ALTER TABLE anomaly_engine_results_v1 ADD COLUMN IF NOT EXISTS triggered_categories_count smallint DEFAULT 0;
ALTER TABLE anomaly_engine_results_v1 ADD COLUMN IF NOT EXISTS is_anomalous boolean DEFAULT false;
ALTER TABLE anomaly_engine_results_v1 ADD COLUMN IF NOT EXISTS evaluation_duration_ms integer DEFAULT 0;
