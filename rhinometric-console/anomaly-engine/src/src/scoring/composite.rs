use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;
use crate::scoring::{availability, error, latency, ssl, trace};

/// Category weights — must sum to 1.0
const W_LATENCY: f64 = 0.30;
const W_AVAILABILITY: f64 = 0.25;
const W_ERROR: f64 = 0.20;
const W_TRACE: f64 = 0.20;
const W_SSL: f64 = 0.05;

/// Result of composite scoring.
pub struct CompositeResult {
    pub score: f64,
    pub latency_score: f64,
    pub availability_score: f64,
    pub error_score: f64,
    pub trace_score: f64,
    pub ssl_score: f64,
    pub reason_codes: Vec<ReasonCode>,
}

/// Compute the composite anomaly score from all category scorers.
///
/// Formula:
///   weighted_sum = L*0.35 + A*0.30 + E*0.25 + S*0.10
///   + correlation_bonus(0–10)
///
/// Correlation bonus: when 2+ non-SSL categories fire (score > 15),
/// add 5–10 points because multi-category degradation is more
/// significant than single-category.
pub fn score(snap: &ServiceSignalSnapshot) -> CompositeResult {
    let (lat_score, mut lat_reasons) = latency::score(snap);
    let (avail_score, mut avail_reasons) = availability::score(snap);
    let (err_score, mut err_reasons) = error::score(snap);
    let (trace_score, mut trace_reasons) = trace::score(snap);
    let (ssl_score, mut ssl_reasons) = ssl::score(snap);

    let weighted = lat_score * W_LATENCY
        + avail_score * W_AVAILABILITY
        + err_score * W_ERROR
        + trace_score * W_TRACE
        + ssl_score * W_SSL;

    let correlation_bonus = compute_correlation_bonus(lat_score, avail_score, err_score, trace_score);

    let final_score = (weighted + correlation_bonus).min(100.0);

    let mut all_reasons = Vec::new();
    all_reasons.append(&mut lat_reasons);
    all_reasons.append(&mut avail_reasons);
    all_reasons.append(&mut err_reasons);
    all_reasons.append(&mut trace_reasons);
    all_reasons.append(&mut ssl_reasons);

    // Sort by severity weight descending
    all_reasons.sort_by(|a, b| {
        b.severity_weight()
            .partial_cmp(&a.severity_weight())
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    CompositeResult {
        score: round2(final_score),
        latency_score: round2(lat_score),
        availability_score: round2(avail_score),
        error_score: round2(err_score),
        trace_score: round2(trace_score),
        ssl_score: round2(ssl_score),
        reason_codes: all_reasons,
    }
}

/// Correlation bonus: multi-category degradation amplifier.
/// Base: operational categories (lat, avail, err) → 0/5/10.
/// Enhanced (V1.4): latency+trace both >30 → +5, error+trace both >30 → +5 (max +10 additional).
fn compute_correlation_bonus(lat: f64, avail: f64, err: f64, trace: f64) -> f64 {
    // Base: operational categories (not SSL, not trace)
    let firing_count = [lat, avail, err]
        .iter()
        .filter(|&&v| v > 15.0)
        .count();

    let base = match firing_count {
        3 => 10.0,
        2 => 5.0,
        _ => 0.0,
    };

    // Enhanced trace correlation (V1.4)
    let mut trace_bonus: f64 = 0.0;
    if lat > 30.0 && trace > 30.0 {
        trace_bonus += 5.0;
    }
    if err > 30.0 && trace > 30.0 {
        trace_bonus += 5.0;
    }

    base + trace_bonus.min(10.0)
}

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;

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

    #[test]
    fn test_healthy_composite() {
        let snap = base_snap();
        let r = score(&snap);
        // Sigmoid produces a small residual (~1.17) even at 0% deviation
        assert!(r.score < 5.0, "Healthy service should have near-zero composite: {}", r.score);
        assert!(r.reason_codes.is_empty());
    }

    #[test]
    fn test_latency_only() {
        let mut snap = base_snap();
        snap.latency_current_ms = 500.0; // 400% deviation
        let r = score(&snap);
        assert!(r.score > 0.0, "Latency issue should produce non-zero composite");
        assert!(r.latency_score > 0.0);
        assert_eq!(r.availability_score, 0.0);
        assert_eq!(r.error_score, 0.0);
    }

    #[test]
    fn test_correlation_bonus() {
        let mut snap = base_snap();
        snap.latency_current_ms = 500.0;  // High latency
        snap.is_up = false;               // Down
        snap.health_score = 30.0;         // Low health
        snap.consecutive_failures = 5;    // Failure streak
        snap.error_rate_1h = 0.25;        // High error rate
        let r = score(&snap);
        // Should have correlation bonus since lat > 15, avail > 15, err > 15
        assert!(r.score > 50.0, "Multi-category degradation should be severe: {}", r.score);
    }

    #[test]
    fn test_ssl_only_low_weight() {
        let mut snap = base_snap();
        snap.ssl_expiry_days = 5.0; // Expiring soon
        let r = score(&snap);
        // SSL score=90, weight=0.10 → ~9.0
        assert!(r.score < 15.0, "SSL-only should be modest: {}", r.score);
    }
}
