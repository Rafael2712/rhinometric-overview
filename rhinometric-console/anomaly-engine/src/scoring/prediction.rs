use crate::models::anomaly::{PredictedRiskLevel, PredictionConfidence, PredictionResult};
use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;
use crate::threshold::PredictionConfig;

/// V1.5: Deterministic short-horizon predictive risk scoring.
///
/// This layer runs AFTER anomaly scoring and does NOT replace it.
/// It detects worsening trajectories and estimates near-term operational risk.
///
/// Returns a PredictionResult with score (0–100), risk level, horizon,
/// confidence, reason codes, and human-readable summary.
pub fn predict(snap: &ServiceSignalSnapshot, cfg: &PredictionConfig) -> PredictionResult {
    if !cfg.enabled {
        return PredictionResult {
            predicted_risk_score: 0.0,
            predicted_risk_level: PredictedRiskLevel::None,
            predicted_horizon_minutes: None,
            prediction_confidence: PredictionConfidence::Low,
            prediction_reason_codes: vec![],
            prediction_summary: "Prediction disabled".into(),
        };
    }

    let mut reasons = Vec::new();

    // ── Component scores ──
    let lat_score = predict_latency(snap, cfg, &mut reasons);
    let err_score = predict_error(snap, cfg, &mut reasons);
    let avail_score = predict_availability(snap, cfg, &mut reasons);
    let trace_score = predict_trace(snap, cfg, &mut reasons);
    let ssl_score = predict_ssl(snap, cfg, &mut reasons);

    // ── Correlation bonus ──
    let firing_count = [lat_score, err_score, avail_score, trace_score]
        .iter()
        .filter(|&&s| s > 0.0)
        .count();

    let correlation = if firing_count >= 3 {
        reasons.push(ReasonCode::PredictedMultiSignalEscalation {
            firing_signals: firing_count as u32,
        });
        cfg.correlation_bonus_three_signals
    } else if firing_count >= 2 {
        reasons.push(ReasonCode::PredictedMultiSignalEscalation {
            firing_signals: firing_count as u32,
        });
        cfg.correlation_bonus_two_signals
    } else {
        0.0
    };

    let raw = lat_score + err_score + avail_score + trace_score + ssl_score + correlation;
    let predicted_risk_score = round2(raw.clamp(0.0, 100.0));
    let predicted_risk_level = PredictedRiskLevel::from_score(predicted_risk_score);

    // ── Horizon ──
    let predicted_horizon_minutes = compute_horizon(predicted_risk_score, &reasons);

    // ── Confidence ──
    let prediction_confidence = compute_confidence(snap, &reasons, firing_count);

    // ── Summary ──
    let prediction_summary = build_summary(
        predicted_risk_score,
        &predicted_risk_level,
        predicted_horizon_minutes,
        &prediction_confidence,
        &reasons,
    );

    PredictionResult {
        predicted_risk_score,
        predicted_risk_level,
        predicted_horizon_minutes,
        prediction_confidence,
        prediction_reason_codes: reasons,
        prediction_summary,
    }
}

// ────────────────────────────────────────────────────────────────
// Component predictors
// ────────────────────────────────────────────────────────────────

/// Latency prediction: trend slope + r² + baseline proximity.
/// Max contribution: 30.
fn predict_latency(
    snap: &ServiceSignalSnapshot,
    cfg: &PredictionConfig,
    reasons: &mut Vec<ReasonCode>,
) -> f64 {
    if snap.latency_baseline_ms <= 0.0 {
        return 0.0;
    }

    let baseline_ratio = snap.latency_current_ms / snap.latency_baseline_ms;
    let has_trend = snap.latency_trend_slope > cfg.latency_slope_threshold
        && snap.latency_trend_r2 >= cfg.latency_r2_min;

    let mut score: f64 = 0.0;

    if has_trend {
        // Base: trend detected with good fit
        score += 15.0;

        // Amplify if already above baseline
        if baseline_ratio >= cfg.latency_baseline_multiplier_high {
            score += 15.0;
        } else if baseline_ratio >= cfg.latency_baseline_multiplier_warn {
            score += 8.0;
        }
    } else if baseline_ratio >= cfg.latency_baseline_multiplier_high {
        // No strong trend, but latency is already elevated — mild risk
        score += 8.0;
    }

    // Trace P95 amplification: if trace latency >> baseline
    if snap.trace_p95_latency_ms > 0.0
        && snap.latency_baseline_ms > 0.0
        && snap.trace_p95_latency_ms > snap.latency_baseline_ms * 2.0
        && has_trend
    {
        score += 5.0;
    }

    if score > 0.0 {
        reasons.push(ReasonCode::PredictedLatencyDegradation {
            slope: round2(snap.latency_trend_slope),
            r2: round2(snap.latency_trend_r2),
            baseline_ratio: round2(baseline_ratio),
        });
    }

    score.min(30.0)
}

/// Error prediction: burst ratio + error rate pressure + log count.
/// Max contribution: 30.
fn predict_error(
    snap: &ServiceSignalSnapshot,
    cfg: &PredictionConfig,
    reasons: &mut Vec<ReasonCode>,
) -> f64 {
    let mut score: f64 = 0.0;

    // Error burst detection
    if snap.log_error_burst_ratio > cfg.error_burst_ratio_high {
        score += 15.0;
    } else if snap.log_error_burst_ratio > cfg.error_burst_ratio_warn {
        score += 8.0;
    }

    // Error rate pressure
    if snap.error_rate_1h >= cfg.error_rate_high {
        score += 10.0;
    } else if snap.error_rate_1h >= cfg.error_rate_warn {
        score += 5.0;
    }

    // Log error count as early warning
    if snap.log_error_count_1h >= cfg.log_error_count_high {
        score += 8.0;
    } else if snap.log_error_count_1h >= cfg.log_error_count_warn {
        score += 4.0;
    }

    // Warnings as leading indicator (mild)
    if snap.log_warn_count_1h >= 100 {
        score += 3.0;
    }

    if score > 0.0 {
        reasons.push(ReasonCode::PredictedErrorEscalation {
            error_rate: snap.error_rate_1h,
            burst_ratio: snap.log_error_burst_ratio,
            log_error_count: snap.log_error_count_1h,
        });
    }

    score.min(30.0)
}

/// Availability prediction: health drop + consecutive failures + incidents.
/// Max contribution: 30.
fn predict_availability(
    snap: &ServiceSignalSnapshot,
    cfg: &PredictionConfig,
    reasons: &mut Vec<ReasonCode>,
) -> f64 {
    let mut score: f64 = 0.0;

    // Health score below expected healthy baseline (85)
    let health_drop = 85.0 - snap.health_score;
    if health_drop >= cfg.health_score_drop_high {
        score += 15.0;
    } else if health_drop >= cfg.health_score_drop_warn {
        score += 8.0;
    }

    // Consecutive failures as precursor
    if snap.consecutive_failures >= cfg.consecutive_failures_high {
        score += 12.0;
    } else if snap.consecutive_failures >= cfg.consecutive_failures_warn {
        score += 5.0;
    }

    // Recent incidents as pattern indicator
    if snap.incidents_24h >= 3 {
        score += 8.0;
    } else if snap.incidents_24h >= 1 {
        score += 3.0;
    }

    if score > 0.0 {
        reasons.push(ReasonCode::PredictedAvailabilityRisk {
            health_score: snap.health_score,
            consecutive_failures: snap.consecutive_failures,
            incidents_24h: snap.incidents_24h,
        });
    }

    score.min(30.0)
}

/// Trace prediction: bottleneck pressure + slow ops + trace latency.
/// Max contribution: 25.
/// Only fires when trace signals are available.
fn predict_trace(
    snap: &ServiceSignalSnapshot,
    cfg: &PredictionConfig,
    reasons: &mut Vec<ReasonCode>,
) -> f64 {
    let has_traces = snap
        .signals_available
        .iter()
        .any(|s| s.contains("jaeger") || s.contains("trace"));

    if !has_traces && snap.trace_p95_latency_ms == 0.0 && snap.trace_bottleneck_score == 0.0 {
        return 0.0;
    }

    let mut score: f64 = 0.0;

    // Bottleneck pressure
    if snap.trace_bottleneck_score >= cfg.trace_bottleneck_high {
        score += 12.0;
    } else if snap.trace_bottleneck_score >= cfg.trace_bottleneck_warn {
        score += 6.0;
    }

    // Slow operations
    if snap.trace_slow_operations >= cfg.trace_slow_ops_high {
        score += 10.0;
    } else if snap.trace_slow_operations >= cfg.trace_slow_ops_warn {
        score += 5.0;
    }

    // Trace P95 significantly above service baseline
    if snap.latency_baseline_ms > 0.0 && snap.trace_p95_latency_ms > snap.latency_baseline_ms * 2.5
    {
        score += 5.0;
    }

    if score > 0.0 {
        reasons.push(ReasonCode::PredictedTracePressure {
            bottleneck_score: snap.trace_bottleneck_score,
            slow_operations: snap.trace_slow_operations,
            trace_p95_ms: snap.trace_p95_latency_ms,
        });
    }

    score.min(25.0)
}

/// SSL prediction: certificate expiry as forward-looking risk.
/// Max contribution: 10.
fn predict_ssl(
    snap: &ServiceSignalSnapshot,
    cfg: &PredictionConfig,
    reasons: &mut Vec<ReasonCode>,
) -> f64 {
    let mut score = 0.0;

    if snap.ssl_expiry_days <= cfg.ssl_days_high {
        score += 10.0;
        reasons.push(ReasonCode::PredictedSslRisk {
            days_remaining: snap.ssl_expiry_days,
        });
    } else if snap.ssl_expiry_days <= cfg.ssl_days_warn {
        score += 5.0;
        reasons.push(ReasonCode::PredictedSslRisk {
            days_remaining: snap.ssl_expiry_days,
        });
    }

    score
}

// ────────────────────────────────────────────────────────────────
// Horizon, confidence, summary
// ────────────────────────────────────────────────────────────────

/// Compute predicted horizon in minutes.
/// Only 30 / 60 / 120 / None — no fake precision.
fn compute_horizon(risk_score: f64, reasons: &[ReasonCode]) -> Option<u32> {
    if risk_score < 20.0 {
        return None;
    }

    // Strong multi-signal or high score → near-term
    let has_multi = reasons
        .iter()
        .any(|r| matches!(r, ReasonCode::PredictedMultiSignalEscalation { .. }));

    if risk_score >= 60.0 || (risk_score >= 40.0 && has_multi) {
        Some(30)
    } else if risk_score >= 40.0 {
        Some(60)
    } else {
        Some(120)
    }
}

/// Compute prediction confidence.
fn compute_confidence(
    snap: &ServiceSignalSnapshot,
    reasons: &[ReasonCode],
    firing_count: usize,
) -> PredictionConfidence {
    if reasons.is_empty() {
        return PredictionConfidence::Low;
    }

    let mut quality = 0u32;

    // Trend quality: r² indicates how reliable the slope is
    if snap.latency_trend_r2 >= 0.85 {
        quality += 3;
    } else if snap.latency_trend_r2 >= 0.7 {
        quality += 2;
    } else if snap.latency_trend_r2 >= 0.3 {
        quality += 1;
    }

    // Signal agreement
    if firing_count >= 3 {
        quality += 3;
    } else if firing_count >= 2 {
        quality += 2;
    } else {
        quality += 1;
    }

    // Data sufficiency
    if snap.checks_in_last_1h >= 50 {
        quality += 2;
    } else if snap.checks_in_last_1h >= 30 {
        quality += 1;
    }

    // Baseline maturity
    if snap.baseline_age_hours >= 24.0 {
        quality += 2;
    } else if snap.baseline_age_hours >= 12.0 {
        quality += 1;
    }

    // Trace availability bonus
    let has_traces = snap
        .signals_available
        .iter()
        .any(|s| s.contains("jaeger") || s.contains("trace"));
    if has_traces {
        quality += 1;
    }

    match quality {
        0..=3 => PredictionConfidence::Low,
        4..=6 => PredictionConfidence::Medium,
        7..=9 => PredictionConfidence::High,
        _ => PredictionConfidence::VeryHigh,
    }
}

/// Build human-readable prediction summary.
fn build_summary(
    score: f64,
    level: &PredictedRiskLevel,
    horizon: Option<u32>,
    confidence: &PredictionConfidence,
    reasons: &[ReasonCode],
) -> String {
    if reasons.is_empty() || score < 20.0 {
        return "No elevated predicted risk".into();
    }

    let horizon_str = match horizon {
        Some(30) => "within 30 minutes",
        Some(60) => "within 1 hour",
        Some(120) => "within 2 hours",
        _ => "near-term",
    };

    let top_reasons: Vec<String> = reasons.iter().take(3).map(|r| r.label()).collect();

    format!(
        "Predicted risk: {} {} (confidence: {}). {}",
        level.as_str().to_uppercase(),
        horizon_str,
        confidence.as_str(),
        top_reasons.join(". ")
    )
}

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;
    use crate::threshold::PredictionConfig;

    fn base_snap() -> ServiceSignalSnapshot {
        ServiceSignalSnapshot {
            service_name: "test".into(),
            service_id: 1,
            service_type: "http".into(),
            group_name: "Default".into(),
            environment: "test".into(),
            timestamp_ms: 0,
            check_interval_seconds: 60,
            latency_current_ms: 100.0,
            latency_baseline_ms: 100.0,
            latency_p95_ms: 200.0,
            latency_trend_slope: 0.0,
            latency_trend_r2: 0.0,
            is_up: true,
            health_score: 97.0,
            consecutive_failures: 0,
            incidents_24h: 0,
            error_rate_1h: 0.0,
            log_error_count_1h: 0,
            log_warn_count_1h: 0,
            log_error_burst_ratio: 0.0,
            ssl_expiry_days: 365.0,
            trace_p95_latency_ms: 0.0,
            trace_error_rate: 0.0,
            trace_bottleneck_score: 0.0,
            trace_slow_operations: 0,
            baseline_age_hours: 24.0,
            checks_in_last_1h: 60,
            signals_available: vec![],
        }
    }

    fn default_cfg() -> PredictionConfig {
        PredictionConfig::default()
    }

    #[test]
    fn test_healthy_service_no_prediction() {
        let snap = base_snap();
        let r = predict(&snap, &default_cfg());
        assert_eq!(r.predicted_risk_score, 0.0);
        assert!(matches!(r.predicted_risk_level, PredictedRiskLevel::None));
        assert!(r.predicted_horizon_minutes.is_none());
        assert!(r.prediction_reason_codes.is_empty());
    }

    #[test]
    fn test_latency_trend_triggers_prediction() {
        let mut snap = base_snap();
        snap.latency_trend_slope = 0.5;
        snap.latency_trend_r2 = 0.85;
        snap.latency_current_ms = 150.0; // 1.5× baseline → high
        let r = predict(&snap, &default_cfg());
        // slope>0.15 + r2>0.7 → 15, baseline ratio 1.5 → +15 = 30
        assert!(
            r.predicted_risk_score >= 20.0,
            "Latency trend should trigger prediction: {}",
            r.predicted_risk_score
        );
        assert!(!matches!(r.predicted_risk_level, PredictedRiskLevel::None));
    }

    #[test]
    fn test_error_pressure_triggers() {
        let mut snap = base_snap();
        snap.error_rate_1h = 0.10;
        snap.log_error_burst_ratio = 5.0;
        snap.log_error_count_1h = 25;
        let r = predict(&snap, &default_cfg());
        // burst>4 →15, rate≥0.08→10, count≥20→8 = 33 (capped at 30) + no multi
        assert!(
            r.predicted_risk_score >= 20.0,
            "Error pressure should trigger: {}",
            r.predicted_risk_score
        );
    }

    #[test]
    fn test_availability_risk() {
        let mut snap = base_snap();
        snap.health_score = 60.0;
        snap.consecutive_failures = 4;
        snap.incidents_24h = 2;
        let r = predict(&snap, &default_cfg());
        // health drop 25 ≥ 20 → 15, failures 4 ≥ 3 → 12, incidents 2 ≥ 1 → 3 = 30
        assert!(
            r.predicted_risk_score >= 20.0,
            "Availability risk should trigger: {}",
            r.predicted_risk_score
        );
    }

    #[test]
    fn test_trace_prediction() {
        let mut snap = base_snap();
        snap.trace_bottleneck_score = 0.65;
        snap.trace_slow_operations = 3;
        snap.trace_p95_latency_ms = 300.0;
        snap.signals_available = vec!["jaeger_traces".into()];
        let r = predict(&snap, &default_cfg());
        // bottleneck 0.65 ≥ 0.6 → 12, slow 3 ≥ 2 → 5, trace_p95 300 > 2.5*100=250 → 5 = 22
        assert!(
            r.predicted_risk_score >= 20.0,
            "Trace pressure should trigger: {}",
            r.predicted_risk_score
        );
    }

    #[test]
    fn test_ssl_mild() {
        let mut snap = base_snap();
        snap.ssl_expiry_days = 10.0;
        let r = predict(&snap, &default_cfg());
        // 10 days ≤ 14 → 5 points. Not enough for prediction
        assert!(r.predicted_risk_score < 20.0);
        assert!(matches!(r.predicted_risk_level, PredictedRiskLevel::None));
    }

    #[test]
    fn test_multi_signal_correlation() {
        let mut snap = base_snap();
        snap.latency_trend_slope = 0.5;
        snap.latency_trend_r2 = 0.85;
        snap.latency_current_ms = 160.0; // 1.6× baseline
        snap.error_rate_1h = 0.10;
        snap.log_error_burst_ratio = 5.0;
        snap.log_error_count_1h = 25;
        snap.health_score = 60.0;
        snap.consecutive_failures = 4;
        let r = predict(&snap, &default_cfg());
        // lat 30 + err 30 + avail 27 + correlation 15 = ~100 (clamped)
        assert!(
            r.predicted_risk_score >= 60.0,
            "Multi-signal should produce high risk: {}",
            r.predicted_risk_score
        );
        assert!(r.predicted_horizon_minutes == Some(30));
    }

    #[test]
    fn test_prediction_disabled() {
        let snap = base_snap();
        let mut cfg = default_cfg();
        cfg.enabled = false;
        let r = predict(&snap, &cfg);
        assert_eq!(r.predicted_risk_score, 0.0);
        assert_eq!(r.prediction_summary, "Prediction disabled");
    }

    #[test]
    fn test_horizon_values() {
        // score < 20 → None
        assert_eq!(compute_horizon(15.0, &[]), None);
        // score 20-39 → 120
        assert_eq!(
            compute_horizon(25.0, &[ReasonCode::PredictedLatencyDegradation {
                slope: 0.5,
                r2: 0.8,
                baseline_ratio: 1.3,
            }]),
            Some(120)
        );
        // score 40-59 → 60
        assert_eq!(
            compute_horizon(50.0, &[ReasonCode::PredictedLatencyDegradation {
                slope: 0.5,
                r2: 0.8,
                baseline_ratio: 1.5,
            }]),
            Some(60)
        );
        // score ≥ 60 → 30
        assert_eq!(compute_horizon(65.0, &[]), Some(30));
    }

    #[test]
    fn test_confidence_levels() {
        let snap = base_snap();
        // No reasons → Low
        assert!(matches!(
            compute_confidence(&snap, &[], 0),
            PredictionConfidence::Low
        ));

        let reasons = vec![ReasonCode::PredictedLatencyDegradation {
            slope: 0.5,
            r2: 0.8,
            baseline_ratio: 1.5,
        }];

        // Single signal, basic snap
        let c = compute_confidence(&snap, &reasons, 1);
        assert!(matches!(c, PredictionConfidence::Low | PredictionConfidence::Medium));

        // Multi signal + good data
        let mut snap2 = base_snap();
        snap2.latency_trend_r2 = 0.9;
        snap2.checks_in_last_1h = 60;
        snap2.baseline_age_hours = 48.0;
        snap2.signals_available = vec!["jaeger_traces".into()];
        let c2 = compute_confidence(&snap2, &reasons, 3);
        assert!(matches!(
            c2,
            PredictionConfidence::High | PredictionConfidence::VeryHigh
        ));
    }
}
