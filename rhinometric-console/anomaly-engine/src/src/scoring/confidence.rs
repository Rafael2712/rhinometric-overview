use crate::models::snapshot::ServiceSignalSnapshot;

/// Confidence computation using harmonic mean of three quality signals:
///   1. baseline_quality   — how mature is the baseline data?
///   2. data_sufficiency   — are we getting enough data points?
///   3. signal_agreement   — do multiple signals agree on the anomaly direction?
///
/// Harmonic mean penalises any single weak component, which is what we want:
/// if the baseline is immature OR data is sparse, confidence should drop hard.
///
/// Returns a value in [0.0, 1.0].
pub fn compute(snap: &ServiceSignalSnapshot, category_scores: &[f64]) -> f64 {
    let bq = baseline_quality(snap.baseline_age_hours);
    let ds = data_sufficiency(snap.checks_in_last_1h, snap.check_interval_seconds);
    let sa = signal_agreement(category_scores);

    harmonic_mean_3(bq, ds, sa)
}

/// Baseline quality: how old/mature is the rolling baseline?
/// 0h → 0.1 (bootstrap), 6h → 0.5, 24h → 0.9, 48h+ → 1.0
fn baseline_quality(age_hours: f64) -> f64 {
    if age_hours >= 48.0 {
        1.0
    } else if age_hours >= 24.0 {
        0.9
    } else if age_hours >= 12.0 {
        0.7
    } else if age_hours >= 6.0 {
        0.5
    } else if age_hours >= 1.0 {
        0.3
    } else {
        0.1
    }
}

/// Data sufficiency: ratio of actual checks to expected checks in 1h.
/// If check_interval=60s, expect 60 checks/hour. 60/60 = 1.0.
/// If check_interval=300s, expect 12 checks/hour. 12/12 = 1.0.
/// Clamp to [0.1, 1.0].
fn data_sufficiency(checks_in_1h: u32, interval_s: u32) -> f64 {
    let expected = if interval_s > 0 {
        3600.0 / interval_s as f64
    } else {
        60.0 // default to 60s interval
    };

    let ratio = checks_in_1h as f64 / expected;
    ratio.clamp(0.1, 1.0)
}

/// Signal agreement: how many category scores are non-trivial?
/// If all categories agree (all elevated or all zero), confidence is higher.
/// Mixed signals reduce confidence.
fn signal_agreement(scores: &[f64]) -> f64 {
    let n = scores.len();
    let firing = scores.iter().filter(|&&s| s > 15.0).count();
    let quiet = scores.iter().filter(|&&s| s <= 5.0).count();

    // Best case: all agree (all firing or all quiet)
    if quiet == n {
        return 0.95; // healthy = high confidence in normalcy
    }

    match firing {
        f if f == n => 0.95,      // All degraded — strong agreement
        f if f >= n - 1 => 0.85,  // Almost all
        f if f >= n - 2 => 0.70,  // Most
        1 => 0.55,                // Single signal — moderate confidence
        _ => 0.40,                // Edge case: scores in 5-15 range, low agreement
    }
}

/// Harmonic mean of three values, with floor at 0.05.
fn harmonic_mean_3(a: f64, b: f64, c: f64) -> f64 {
    let a = a.max(0.05);
    let b = b.max(0.05);
    let c = c.max(0.05);
    let hm = 3.0 / (1.0 / a + 1.0 / b + 1.0 / c);
    round3(hm.clamp(0.0, 1.0))
}

fn round3(v: f64) -> f64 {
    (v * 1000.0).round() / 1000.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_perfect_confidence() {
        // Mature baseline, full data, all signals agree
        let scores = [50.0, 50.0, 50.0, 50.0];
        let snap = make_snap(48.0, 60, 60);
        let c = compute(&snap, &scores);
        assert!(c >= 0.90, "Perfect conditions: {c}");
    }

    #[test]
    fn test_immature_baseline() {
        let scores = [50.0, 50.0, 50.0, 50.0];
        let snap = make_snap(2.0, 60, 60);
        let c = compute(&snap, &scores);
        // baseline_quality(2h)=0.3, data=1.0, signal_agreement=0.95 → HM≈0.557
        assert!(c < 0.6, "Immature baseline should reduce confidence: {c}");
    }

    #[test]
    fn test_sparse_data() {
        let scores = [50.0, 50.0, 0.0, 0.0];
        let snap = make_snap(48.0, 5, 60); // Only 5 checks when expecting 60
        let c = compute(&snap, &scores);
        assert!(c < 0.5, "Sparse data should reduce confidence: {c}");
    }

    #[test]
    fn test_healthy_service_confidence() {
        let scores = [0.0, 0.0, 0.0, 0.0];
        let snap = make_snap(48.0, 60, 60);
        let c = compute(&snap, &scores);
        assert!(c >= 0.85, "Healthy service with good data: {c}");
    }

    fn make_snap(baseline_age: f64, checks: u32, interval: u32) -> ServiceSignalSnapshot {
        ServiceSignalSnapshot {
            service_name: "test".into(),
            service_id: 1,
            service_type: "http".into(),
            group_name: "Default".into(),
            environment: "test".into(),
            timestamp_ms: 0,
            check_interval_seconds: interval,
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
            baseline_age_hours: baseline_age,
            checks_in_last_1h: checks,
            signals_available: vec![],
        }
    }
}
