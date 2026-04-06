CREATE UNIQUE INDEX IF NOT EXISTS idx_aev1_svc_fp_active ON anomaly_engine_results_v1 (service_id, fingerprint) WHERE status = 'active';
