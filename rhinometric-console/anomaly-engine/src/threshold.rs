use serde::Deserialize;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Hot-reloadable threshold configuration.
#[derive(Debug, Clone, Deserialize)]
pub struct ThresholdConfig {
    pub scoring: ScoringConfig,
    pub severity: SeverityConfig,
    pub confidence: ConfidenceConfig,
    #[serde(default)]
    pub prediction: PredictionConfig,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ScoringConfig {
    pub active_threshold: f64,
    pub anomalous_threshold: f64,
    pub weights: WeightConfig,
    pub category_trigger_threshold: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct WeightConfig {
    pub latency: f64,
    pub availability: f64,
    pub error: f64,
    pub trace: f64,
    pub ssl: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SeverityConfig {
    pub normal_max: f64,
    pub watch_max: f64,
    pub degraded_max: f64,
    pub critical_max: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ConfidenceConfig {
    pub min_baseline_hours: f64,
    pub min_checks_1h: u32,
}

/// V1.5: Predictive risk layer configuration.
#[derive(Debug, Clone, Deserialize)]
pub struct PredictionConfig {
    #[serde(default = "default_true")]
    pub enabled: bool,

    // Latency prediction
    #[serde(default = "default_latency_slope")]
    pub latency_slope_threshold: f64,
    #[serde(default = "default_latency_r2")]
    pub latency_r2_min: f64,
    #[serde(default = "default_lat_mult_warn")]
    pub latency_baseline_multiplier_warn: f64,
    #[serde(default = "default_lat_mult_high")]
    pub latency_baseline_multiplier_high: f64,

    // Error prediction
    #[serde(default = "default_burst_warn")]
    pub error_burst_ratio_warn: f64,
    #[serde(default = "default_burst_high")]
    pub error_burst_ratio_high: f64,
    #[serde(default = "default_err_rate_warn")]
    pub error_rate_warn: f64,
    #[serde(default = "default_err_rate_high")]
    pub error_rate_high: f64,
    #[serde(default = "default_log_err_warn")]
    pub log_error_count_warn: u64,
    #[serde(default = "default_log_err_high")]
    pub log_error_count_high: u64,

    // Availability prediction
    #[serde(default = "default_health_warn")]
    pub health_score_drop_warn: f64,
    #[serde(default = "default_health_high")]
    pub health_score_drop_high: f64,
    #[serde(default = "default_fail_warn")]
    pub consecutive_failures_warn: u32,
    #[serde(default = "default_fail_high")]
    pub consecutive_failures_high: u32,

    // Trace prediction
    #[serde(default = "default_bn_warn")]
    pub trace_bottleneck_warn: f64,
    #[serde(default = "default_bn_high")]
    pub trace_bottleneck_high: f64,
    #[serde(default = "default_slow_warn")]
    pub trace_slow_ops_warn: u32,
    #[serde(default = "default_slow_high")]
    pub trace_slow_ops_high: u32,

    // SSL prediction
    #[serde(default = "default_ssl_warn")]
    pub ssl_days_warn: f64,
    #[serde(default = "default_ssl_high")]
    pub ssl_days_high: f64,

    // Correlation bonus
    #[serde(default = "default_corr_two")]
    pub correlation_bonus_two_signals: f64,
    #[serde(default = "default_corr_three")]
    pub correlation_bonus_three_signals: f64,
}

fn default_true() -> bool { true }
fn default_latency_slope() -> f64 { 0.15 }
fn default_latency_r2() -> f64 { 0.7 }
fn default_lat_mult_warn() -> f64 { 1.25 }
fn default_lat_mult_high() -> f64 { 1.5 }
fn default_burst_warn() -> f64 { 2.5 }
fn default_burst_high() -> f64 { 4.0 }
fn default_err_rate_warn() -> f64 { 0.03 }
fn default_err_rate_high() -> f64 { 0.08 }
fn default_log_err_warn() -> u64 { 5 }
fn default_log_err_high() -> u64 { 20 }
fn default_health_warn() -> f64 { 10.0 }
fn default_health_high() -> f64 { 20.0 }
fn default_fail_warn() -> u32 { 1 }
fn default_fail_high() -> u32 { 3 }
fn default_bn_warn() -> f64 { 0.4 }
fn default_bn_high() -> f64 { 0.6 }
fn default_slow_warn() -> u32 { 2 }
fn default_slow_high() -> u32 { 5 }
fn default_ssl_warn() -> f64 { 14.0 }
fn default_ssl_high() -> f64 { 7.0 }
fn default_corr_two() -> f64 { 10.0 }
fn default_corr_three() -> f64 { 15.0 }

impl Default for PredictionConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            latency_slope_threshold: 0.15,
            latency_r2_min: 0.7,
            latency_baseline_multiplier_warn: 1.25,
            latency_baseline_multiplier_high: 1.5,
            error_burst_ratio_warn: 2.5,
            error_burst_ratio_high: 4.0,
            error_rate_warn: 0.03,
            error_rate_high: 0.08,
            log_error_count_warn: 5,
            log_error_count_high: 20,
            health_score_drop_warn: 10.0,
            health_score_drop_high: 20.0,
            consecutive_failures_warn: 1,
            consecutive_failures_high: 3,
            trace_bottleneck_warn: 0.4,
            trace_bottleneck_high: 0.6,
            trace_slow_ops_warn: 2,
            trace_slow_ops_high: 5,
            ssl_days_warn: 14.0,
            ssl_days_high: 7.0,
            correlation_bonus_two_signals: 10.0,
            correlation_bonus_three_signals: 15.0,
        }
    }
}

impl Default for ThresholdConfig {
    fn default() -> Self {
        Self {
            scoring: ScoringConfig {
                active_threshold: 15.0,
                anomalous_threshold: 35.0,
                weights: WeightConfig {
                    latency: 0.30,
                    availability: 0.25,
                    error: 0.20,
                    trace: 0.20,
                    ssl: 0.05,
                },
                category_trigger_threshold: 15.0,
            },
            severity: SeverityConfig {
                normal_max: 15.0,
                watch_max: 35.0,
                degraded_max: 60.0,
                critical_max: 80.0,
            },
            confidence: ConfidenceConfig {
                min_baseline_hours: 12.0,
                min_checks_1h: 30,
            },
            prediction: PredictionConfig::default(),
        }
    }
}

/// Thread-safe, hot-reloadable config holder.
pub type SharedThresholdConfig = Arc<RwLock<ThresholdConfig>>;

/// Load config from YAML file, fallback to defaults.
pub fn load_from_file(path: &str) -> ThresholdConfig {
    match std::fs::read_to_string(path) {
        Ok(contents) => match serde_yaml::from_str(&contents) {
            Ok(cfg) => {
                tracing::info!("Loaded threshold config from {path}");
                cfg
            }
            Err(e) => {
                tracing::warn!("Failed to parse {path}: {e} — using defaults");
                ThresholdConfig::default()
            }
        },
        Err(_) => {
            tracing::info!("No config file at {path} — using defaults");
            ThresholdConfig::default()
        }
    }
}

/// Reload config from disk (called each cycle for hot-reload).
pub async fn reload(shared: &SharedThresholdConfig, path: &str) {
    let new_cfg = load_from_file(path);
    let mut cfg = shared.write().await;
    *cfg = new_cfg;
}
