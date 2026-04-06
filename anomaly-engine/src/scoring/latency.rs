use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;

/// Latency category scorer.
/// Weight: 0.30 of composite.
///
/// Inputs: latency_current_ms, latency_baseline_ms, latency_p95_ms
/// Score range: 0–100
pub fn score(snap: &ServiceSignalSnapshot) -> (f64, Vec<ReasonCode>) {
    let mut reasons = Vec::new();

    if snap.latency_baseline_ms <= 0.0 {
        return (0.0, reasons);
    }

    let deviation_ratio =
        (snap.latency_current_ms - snap.latency_baseline_ms) / snap.latency_baseline_ms;
    let deviation_pct = deviation_ratio * 100.0;

    // Sigmoid curve: 0 at 0% deviation, ~50 at 100%, ~90 at 300%
    let raw = deviation_pct;
    let mut score = 100.0 / (1.0 + (-0.04_f64 * (raw - 80.0)).exp());

    // P95 amplifier: if current exceeds p95, add urgency bonus
    if snap.latency_p95_ms > 0.0 && snap.latency_current_ms > snap.latency_p95_ms {
        score = (score + 15.0).min(100.0);
        reasons.push(ReasonCode::LatencyAboveP95 {
            current_ms: round2(snap.latency_current_ms),
            p95_ms: round2(snap.latency_p95_ms),
        });
    }

    // Absolute high latency threshold (1000ms)
    if snap.latency_current_ms > 1000.0 {
        score = (score + 10.0).min(100.0);
        reasons.push(ReasonCode::LatencyHigh {
            current_ms: round2(snap.latency_current_ms),
            threshold_ms: 1000.0,
        });
    }

    // Baseline breach reason code (if deviation > 30%)
    if deviation_pct > 30.0 {
        reasons.push(ReasonCode::LatencyBaselineBreach {
            deviation_pct: round2(deviation_pct),
            baseline_ms: round2(snap.latency_baseline_ms),
        });
    }

    let score = score.clamp(0.0, 100.0);
    (score, reasons)
}

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;

    fn make_snap(current: f64, baseline: f64, p95: f64) -> ServiceSignalSnapshot {
        ServiceSignalSnapshot {
            service_name: "test".into(),
            service_id: 1,
            service_type: "http".into(),
            group_name: "Default".into(),
            environment: "test".into(),
            timestamp_ms: 0,
            check_interval_seconds: 60,
            latency_current_ms: current,
            latency_baseline_ms: baseline,
            latency_p95_ms: p95,
            is_up: true,
            health_score: 100.0,
            consecutive_failures: 0,
            incidents_24h: 0,
            error_rate_1h: 0.0,
            log_error_count_1h: 0,
            log_warn_count_1h: 0,
            ssl_expiry_days: 365.0,
            baseline_age_hours: 24.0,
            checks_in_last_1h: 60,
            signals_available: vec!["prometheus".into(), "postgresql".into()],
        }
    }

    #[test]
    fn test_normal_latency() {
        let snap = make_snap(170.0, 173.0, 254.0);
        let (score, reasons) = score(&snap);
        assert!(score < 15.0, "Normal latency should score low, got {score}");
        assert!(reasons.is_empty());
    }

    #[test]
    fn test_2x_baseline() {
        let snap = make_snap(346.0, 173.0, 254.0);
        let (s, reasons) = score(&snap);
        assert!(s > 30.0, "2× baseline should score significant, got {s}");
        assert!(!reasons.is_empty());
    }

    #[test]
    fn test_zero_baseline() {
        let snap = make_snap(500.0, 0.0, 0.0);
        let (s, _) = score(&snap);
        assert_eq!(s, 0.0, "Zero baseline should return 0");
    }

    #[test]
    fn test_above_p95() {
        let snap = make_snap(300.0, 173.0, 254.0);
        let (_, reasons) = score(&snap);
        let has_p95 = reasons
            .iter()
            .any(|r| matches!(r, ReasonCode::LatencyAboveP95 { .. }));
        assert!(has_p95, "Should have P95 reason code");
    }

    #[test]
    fn test_high_absolute() {
        let snap = make_snap(1200.0, 400.0, 800.0);
        let (_, reasons) = score(&snap);
        let has_high = reasons
            .iter()
            .any(|r| matches!(r, ReasonCode::LatencyHigh { .. }));
        assert!(has_high, "Should have LatencyHigh reason code");
    }
}
