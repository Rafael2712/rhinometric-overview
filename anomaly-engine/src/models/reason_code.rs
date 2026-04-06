use serde::{Deserialize, Serialize};

/// Self-documenting reason codes with evidence values.
/// Each variant carries the data that triggered it.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "code", content = "detail")]
pub enum ReasonCode {
    // ── Latency (5 variants) ──
    LatencyBaselineBreach {
        deviation_pct: f64,
        baseline_ms: f64,
    },
    LatencyAboveP95 {
        current_ms: f64,
        p95_ms: f64,
    },
    LatencyHigh {
        current_ms: f64,
        threshold_ms: f64,
    },
    /// V1.3: latency trend is degrading (positive slope + high R²)
    LatencyTrendDegrading {
        slope: f64,
        r2: f64,
    },
    /// V1.3: latency trend is recovering (negative slope + high R²)
    LatencyTrendRecovery {
        slope: f64,
        r2: f64,
    },

    // ── Availability (4 variants) ──
    ServiceDown {
        consecutive_failures: u32,
    },
    HealthScoreLow {
        score: f64,
        baseline: f64,
    },
    UptimeDegraded {
        incidents_24h: u32,
    },
    FailureStreak {
        count: u32,
    },

    // ── Error (4 variants) ──
    ErrorRateElevated {
        rate: f64,
        threshold: f64,
    },
    LogErrorSurge {
        count: u64,
        window: String,
    },
    LogWarningSurge {
        count: u64,
        window: String,
    },
    /// V1.3: short-term error burst vs hourly baseline
    ErrorBurstDetected {
        burst_ratio: f64,
    },

    // ── SSL (2 variants) — risk signal, not operational anomaly ──
    SslExpirySoon {
        days_remaining: f64,
    },
    SslExpired,
}

impl ReasonCode {
    /// Human-readable label for evidence summary.
    pub fn label(&self) -> String {
        match self {
            ReasonCode::LatencyBaselineBreach { deviation_pct, baseline_ms } => {
                format!("Latency Baseline Breach (+{:.0}% vs {:.0}ms baseline)", deviation_pct, baseline_ms)
            }
            ReasonCode::LatencyAboveP95 { current_ms, p95_ms } => {
                format!("Latency Above P95 ({:.0}ms > {:.0}ms P95)", current_ms, p95_ms)
            }
            ReasonCode::LatencyHigh { current_ms, threshold_ms } => {
                format!("High Latency ({:.0}ms > {:.0}ms threshold)", current_ms, threshold_ms)
            }
            ReasonCode::LatencyTrendDegrading { slope, r2 } => {
                format!("Latency Trend Degrading (slope={:.2}, r²={:.2})", slope, r2)
            }
            ReasonCode::LatencyTrendRecovery { slope, r2 } => {
                format!("Latency Trend Recovery (slope={:.2}, r²={:.2})", slope, r2)
            }
            ReasonCode::ServiceDown { consecutive_failures } => {
                format!("Service Down ({} consecutive failures)", consecutive_failures)
            }
            ReasonCode::HealthScoreLow { score, baseline } => {
                format!("Low Health Score ({:.1} below {:.0} baseline)", score, baseline)
            }
            ReasonCode::UptimeDegraded { incidents_24h } => {
                format!("Uptime Degraded ({} incidents in 24h)", incidents_24h)
            }
            ReasonCode::FailureStreak { count } => {
                format!("Failure Streak ({} consecutive)", count)
            }
            ReasonCode::ErrorRateElevated { rate, threshold } => {
                format!("Error Rate Elevated ({:.1}% > {:.1}% threshold)", rate * 100.0, threshold * 100.0)
            }
            ReasonCode::LogErrorSurge { count, window } => {
                format!("Log Error Surge ({} errors in {})", count, window)
            }
            ReasonCode::LogWarningSurge { count, window } => {
                format!("Log Warning Surge ({} warnings in {})", count, window)
            }
            ReasonCode::ErrorBurstDetected { burst_ratio } => {
                format!("Error Burst Detected ({:.1}x normal rate)", burst_ratio)
            }
            ReasonCode::SslExpirySoon { days_remaining } => {
                format!("SSL Expiry Soon ({:.1} days remaining) [risk signal]", days_remaining)
            }
            ReasonCode::SslExpired => {
                "SSL Certificate Expired [risk signal]".to_string()
            }
        }
    }

    /// Approximate severity contribution weight for ordering.
    pub fn severity_weight(&self) -> u32 {
        match self {
            ReasonCode::ServiceDown { .. } => 30,
            ReasonCode::LatencyBaselineBreach { .. } => 25,
            ReasonCode::ErrorRateElevated { .. } => 22,
            ReasonCode::HealthScoreLow { .. } => 20,
            ReasonCode::FailureStreak { .. } => 18,
            ReasonCode::LogErrorSurge { .. } => 15,
            ReasonCode::LatencyTrendDegrading { .. } => 16,
            ReasonCode::LatencyAboveP95 { .. } => 14,
            ReasonCode::LatencyHigh { .. } => 12,
            ReasonCode::ErrorBurstDetected { .. } => 11,
            ReasonCode::LatencyTrendRecovery { .. } => 2,
            ReasonCode::UptimeDegraded { .. } => 10,
            ReasonCode::SslExpired => 8,
            ReasonCode::SslExpirySoon { .. } => 5,
            ReasonCode::LogWarningSurge { .. } => 3,
        }
    }
}
