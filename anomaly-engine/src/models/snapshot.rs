use serde::{Deserialize, Serialize};

/// Input snapshot from the Python backend signal assembler.
/// One per service per evaluation cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceSignalSnapshot {
    // ── Identity ──
    pub service_name: String,
    pub service_id: i64,
    pub service_type: String,
    pub group_name: String,
    pub environment: String,
    pub timestamp_ms: i64,
    pub check_interval_seconds: u32,

    // ── Latency Signals ──
    pub latency_current_ms: f64,
    pub latency_baseline_ms: f64,
    pub latency_p95_ms: f64,

    // ── Latency Trend (V1.3) ──
    #[serde(default)]
    pub latency_trend_slope: f64,
    #[serde(default)]
    pub latency_trend_r2: f64,

    // ── Availability Signals ──
    pub is_up: bool,
    pub health_score: f64,
    pub consecutive_failures: u32,
    pub incidents_24h: u32,

    // ── Error Signals ──
    pub error_rate_1h: f64,
    pub log_error_count_1h: u64,
    pub log_warn_count_1h: u64,

    // ── Error Burst (V1.3) ──
    #[serde(default)]
    pub log_error_burst_ratio: f64,

    // ── SSL ──
    pub ssl_expiry_days: f64,

    // ── Metadata for confidence ──
    pub baseline_age_hours: f64,
    pub checks_in_last_1h: u32,
    pub signals_available: Vec<String>,
}

/// Response wrapper from the signal assembler endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotResponse {
    pub snapshots: Vec<ServiceSignalSnapshot>,
    pub assembled_at: String,
    pub assembly_duration_ms: f64,
    #[serde(default)]
    pub warnings: Vec<String>,
}
