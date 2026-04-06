use serde::{Deserialize, Serialize};
use std::fmt;

/// Anomaly severity levels.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Normal,
    Watch,
    Degraded,
    Critical,
    Emergency,
}

impl Severity {
    pub fn from_score(score: f64) -> Self {
        match score as u32 {
            0..=15 => Severity::Normal,
            16..=35 => Severity::Watch,
            36..=60 => Severity::Degraded,
            61..=80 => Severity::Critical,
            _ => Severity::Emergency,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Severity::Normal => "normal",
            Severity::Watch => "watch",
            Severity::Degraded => "degraded",
            Severity::Critical => "critical",
            Severity::Emergency => "emergency",
        }
    }

    /// Whether this severity level requires latch protection.
    pub fn is_latched(&self) -> bool {
        matches!(self, Severity::Critical | Severity::Emergency)
    }
}

impl fmt::Display for Severity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Confidence label derived from composite confidence score.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ConfidenceLabel {
    Low,
    Medium,
    High,
    VeryHigh,
}

impl ConfidenceLabel {
    pub fn from_score(confidence: f64) -> Self {
        match confidence {
            c if c >= 0.85 => ConfidenceLabel::VeryHigh,
            c if c >= 0.60 => ConfidenceLabel::High,
            c if c >= 0.30 => ConfidenceLabel::Medium,
            _ => ConfidenceLabel::Low,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            ConfidenceLabel::Low => "low",
            ConfidenceLabel::Medium => "medium",
            ConfidenceLabel::High => "high",
            ConfidenceLabel::VeryHigh => "very_high",
        }
    }
}

impl fmt::Display for ConfidenceLabel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Anomaly category identifiers.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AnomalyCategory {
    Latency,
    Availability,
    Error,
    Ssl,
}

impl AnomalyCategory {
    pub fn as_str(&self) -> &'static str {
        match self {
            AnomalyCategory::Latency => "latency",
            AnomalyCategory::Availability => "availability",
            AnomalyCategory::Error => "error",
            AnomalyCategory::Ssl => "ssl",
        }
    }
}

impl fmt::Display for AnomalyCategory {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}
