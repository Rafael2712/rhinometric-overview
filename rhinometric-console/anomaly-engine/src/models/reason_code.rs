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

    // ── Trace (3 variants) ──
    /// V1.4: trace critical-path bottleneck dominance
    TraceBottleneck {
        score: f64,
        threshold: f64,
    },
    /// V1.4: trace-level error rate
    TraceErrorRate {
        rate: f64,
        threshold: f64,
    },
    /// V1.4: slow operations detected in traces
    TraceSlowOperations {
        count: u32,
        threshold: u32,
    },

    // ── SSL (2 variants) — risk signal, not operational anomaly ──
    SslExpirySoon {
        days_remaining: f64,
    },
    SslExpired,

    // ── Prediction (V1.5) — predictive risk reason codes ──
    PredictedLatencyDegradation {
        slope: f64,
        r2: f64,
        baseline_ratio: f64,
    },
    PredictedErrorEscalation {
        error_rate: f64,
        burst_ratio: f64,
        log_error_count: u64,
    },
    PredictedAvailabilityRisk {
        health_score: f64,
        consecutive_failures: u32,
        incidents_24h: u32,
    },
    PredictedTracePressure {
        bottleneck_score: f64,
        slow_operations: u32,
        trace_p95_ms: f64,
    },
    PredictedSslRisk {
        days_remaining: f64,
    },
    PredictedMultiSignalEscalation {
        firing_signals: u32,
    },
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
            ReasonCode::TraceBottleneck { score, threshold } => {
                format!("Trace Bottleneck ({:.0}% dominance, threshold {:.0}%)", score * 100.0, threshold * 100.0)
            }
            ReasonCode::TraceErrorRate { rate, threshold } => {
                format!("Trace Error Rate ({:.1}% > {:.1}% threshold)", rate * 100.0, threshold * 100.0)
            }
            ReasonCode::TraceSlowOperations { count, threshold } => {
                format!("Trace Slow Operations ({} ops, threshold {})", count, threshold)
            }
            ReasonCode::SslExpirySoon { days_remaining } => {
                format!("SSL Expiry Soon ({:.1} days remaining) [risk signal]", days_remaining)
            }
            ReasonCode::SslExpired => {
                "SSL Certificate Expired [risk signal]".to_string()
            }
            ReasonCode::PredictedLatencyDegradation { slope, r2, baseline_ratio } => {
                format!("Predicted Latency Degradation (slope={:.2}, r²={:.2}, {:.0}% above baseline)", slope, r2, (baseline_ratio - 1.0) * 100.0)
            }
            ReasonCode::PredictedErrorEscalation { error_rate, burst_ratio, log_error_count } => {
                format!("Predicted Error Escalation (rate={:.1}%, burst={:.1}x, {} errors)", error_rate * 100.0, burst_ratio, log_error_count)
            }
            ReasonCode::PredictedAvailabilityRisk { health_score, consecutive_failures, incidents_24h } => {
                format!("Predicted Availability Risk (health={:.1}, failures={}, incidents={})", health_score, consecutive_failures, incidents_24h)
            }
            ReasonCode::PredictedTracePressure { bottleneck_score, slow_operations, trace_p95_ms } => {
                format!("Predicted Trace Pressure (bottleneck={:.0}%, slow_ops={}, p95={:.0}ms)", bottleneck_score * 100.0, slow_operations, trace_p95_ms)
            }
            ReasonCode::PredictedSslRisk { days_remaining } => {
                format!("Predicted SSL Risk ({:.0} days until expiry)", days_remaining)
            }
            ReasonCode::PredictedMultiSignalEscalation { firing_signals } => {
                format!("Predicted Multi-Signal Escalation ({} correlated signals)", firing_signals)
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
            ReasonCode::TraceBottleneck { .. } => 20,
            ReasonCode::TraceErrorRate { .. } => 17,
            ReasonCode::TraceSlowOperations { .. } => 13,
            ReasonCode::LatencyTrendRecovery { .. } => 2,
            ReasonCode::UptimeDegraded { .. } => 10,
            ReasonCode::SslExpired => 8,
            ReasonCode::SslExpirySoon { .. } => 5,
            ReasonCode::LogWarningSurge { .. } => 3,
            ReasonCode::PredictedLatencyDegradation { .. } => 14,
            ReasonCode::PredictedErrorEscalation { .. } => 13,
            ReasonCode::PredictedAvailabilityRisk { .. } => 12,
            ReasonCode::PredictedTracePressure { .. } => 11,
            ReasonCode::PredictedSslRisk { .. } => 4,
            ReasonCode::PredictedMultiSignalEscalation { .. } => 15,
        }
    }
}
