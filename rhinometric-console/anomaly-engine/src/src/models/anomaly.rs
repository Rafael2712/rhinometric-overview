use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::reason_code::ReasonCode;
use super::severity::{ConfidenceLabel, Severity};

/// Category score breakdown.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoryScores {
    pub latency: f64,
    pub availability: f64,
    pub error: f64,
    pub trace: f64,
    pub ssl: f64,
}

/// V1.5: Predicted risk level.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PredictedRiskLevel {
    None,
    Low,
    Medium,
    High,
    Critical,
}

impl PredictedRiskLevel {
    pub fn from_score(score: f64) -> Self {
        match score as u32 {
            0..=19 => PredictedRiskLevel::None,
            20..=39 => PredictedRiskLevel::Low,
            40..=59 => PredictedRiskLevel::Medium,
            60..=79 => PredictedRiskLevel::High,
            _ => PredictedRiskLevel::Critical,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            PredictedRiskLevel::None => "none",
            PredictedRiskLevel::Low => "low",
            PredictedRiskLevel::Medium => "medium",
            PredictedRiskLevel::High => "high",
            PredictedRiskLevel::Critical => "critical",
        }
    }
}

/// V1.5: Prediction confidence label.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PredictionConfidence {
    Low,
    Medium,
    High,
    VeryHigh,
}

impl PredictionConfidence {
    pub fn as_str(&self) -> &'static str {
        match self {
            PredictionConfidence::Low => "low",
            PredictionConfidence::Medium => "medium",
            PredictionConfidence::High => "high",
            PredictionConfidence::VeryHigh => "very_high",
        }
    }
}

/// V1.5: Prediction result from the predictive risk layer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionResult {
    pub predicted_risk_score: f64,
    pub predicted_risk_level: PredictedRiskLevel,
    pub predicted_horizon_minutes: Option<u32>,
    pub prediction_confidence: PredictionConfidence,
    pub prediction_reason_codes: Vec<ReasonCode>,
    pub prediction_summary: String,
}

/// Complete anomaly output per service per evaluation cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnomalyOutput {
    pub id: Uuid,
    pub service_id: i64,
    pub service_name: String,
    pub service_type: String,
    pub group_name: String,
    pub environment: String,

    // Scoring
    pub score: f64,
    pub severity: Severity,
    pub confidence: f64,
    pub confidence_label: ConfidenceLabel,

    // Category breakdown
    pub category_scores: CategoryScores,

    // Explainability
    pub reason_codes: Vec<ReasonCode>,
    pub evidence_summary: String,

    // Lifecycle
    pub status: AnomalyStatus,
    pub fingerprint: String,
    pub evaluated_at: DateTime<Utc>,
    pub first_seen: DateTime<Utc>,
    pub last_seen: DateTime<Utc>,
    pub occurrence_count: u32,

    // Validation fields (V1.1)
    pub baseline_deviation_pct: f64,
    pub triggered_categories_count: i16,
    pub is_anomalous: bool,
    pub evaluation_duration_ms: i32,

    // Signal enrichment (V1.3)
    pub latency_trend_slope: f64,
    pub latency_trend_r2: f64,
    pub log_error_burst_ratio: f64,

    // Trace signals (V1.4)
    pub trace_p95_latency_ms: f64,
    pub trace_error_rate: f64,
    pub trace_bottleneck_score: f64,
    pub trace_slow_operations: u32,

    // Prediction (V1.5)
    pub predicted_risk_score: f64,
    pub predicted_risk_level: PredictedRiskLevel,
    pub predicted_horizon_minutes: Option<u32>,
    pub prediction_confidence: PredictionConfidence,
    pub prediction_reason_codes: Vec<ReasonCode>,
    pub prediction_summary: String,
}

/// Anomaly lifecycle states.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AnomalyStatus {
    Active,
    Resolved,
    Suppressed,
}

impl AnomalyStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            AnomalyStatus::Active => "active",
            AnomalyStatus::Resolved => "resolved",
            AnomalyStatus::Suppressed => "suppressed",
        }
    }
}

/// API response for anomaly summary.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnomalySummary {
    pub total_active: u32,
    pub severity_counts: SeverityCounts,
    pub max_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeverityCounts {
    pub normal: u32,
    pub watch: u32,
    pub degraded: u32,
    pub critical: u32,
    pub emergency: u32,
}
