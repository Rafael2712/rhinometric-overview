use serde::Deserialize;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Hot-reloadable threshold configuration.
#[derive(Debug, Clone, Deserialize)]
pub struct ThresholdConfig {
    pub scoring: ScoringConfig,
    pub severity: SeverityConfig,
    pub confidence: ConfidenceConfig,
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

impl Default for ThresholdConfig {
    fn default() -> Self {
        Self {
            scoring: ScoringConfig {
                active_threshold: 15.0,
                anomalous_threshold: 35.0,
                weights: WeightConfig {
                    latency: 0.35,
                    availability: 0.30,
                    error: 0.25,
                    ssl: 0.10,
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
