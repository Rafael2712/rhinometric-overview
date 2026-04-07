use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;

/// Error category scorer.
/// Weight: 0.25 of composite.
///
/// Inputs: error_rate_1h, log_error_count_1h, log_warn_count_1h
/// Score range: 0–100
///
/// NOTE: log_warn_count_1h uses CONSERVATIVE thresholds (0–10 range)
/// to minimise false positives. Tuned per user direction.
pub fn score(snap: &ServiceSignalSnapshot) -> (f64, Vec<ReasonCode>) {
    let mut base: f64 = 0.0;
    let mut reasons = Vec::new();

    // Error rate component (0–50)
    if snap.error_rate_1h >= 0.20 {
        base += 50.0;
        reasons.push(ReasonCode::ErrorRateElevated {
            rate: round2(snap.error_rate_1h),
            threshold: 0.05,
        });
    } else if snap.error_rate_1h >= 0.10 {
        base += 35.0;
        reasons.push(ReasonCode::ErrorRateElevated {
            rate: round2(snap.error_rate_1h),
            threshold: 0.05,
        });
    } else if snap.error_rate_1h >= 0.05 {
        base += 20.0;
        reasons.push(ReasonCode::ErrorRateElevated {
            rate: round2(snap.error_rate_1h),
            threshold: 0.05,
        });
    } else if snap.error_rate_1h >= 0.01 {
        base += 8.0;
    }

    // Log error count component (0–30)
    if snap.log_error_count_1h >= 50 {
        base += 30.0;
        reasons.push(ReasonCode::LogErrorSurge {
            count: snap.log_error_count_1h,
            window: "1h".into(),
        });
    } else if snap.log_error_count_1h >= 20 {
        base += 20.0;
        reasons.push(ReasonCode::LogErrorSurge {
            count: snap.log_error_count_1h,
            window: "1h".into(),
        });
    } else if snap.log_error_count_1h >= 5 {
        base += 10.0;
        reasons.push(ReasonCode::LogErrorSurge {
            count: snap.log_error_count_1h,
            window: "1h".into(),
        });
    } else if snap.log_error_count_1h >= 1 {
        base += 3.0;
    }

    // Log warn count component (0–10) — CONSERVATIVE
    // Thresholds: ≥200→10, ≥100→6, ≥50→3, else→0
    if snap.log_warn_count_1h >= 200 {
        base += 10.0;
        reasons.push(ReasonCode::LogWarningSurge {
            count: snap.log_warn_count_1h,
            window: "1h".into(),
        });
    } else if snap.log_warn_count_1h >= 100 {
        base += 6.0;
        reasons.push(ReasonCode::LogWarningSurge {
            count: snap.log_warn_count_1h,
            window: "1h".into(),
        });
    } else if snap.log_warn_count_1h >= 50 {
        base += 3.0;
    }

    // ── Error burst detection (V1.3) ──
    // burst_ratio = error_5m / (error_1h / 12)
    // If recent 5-min error rate is 3x+ the hourly average → short-term spike
    if snap.log_error_burst_ratio > 3.0 {
        base += 15.0;
        reasons.push(ReasonCode::ErrorBurstDetected {
            burst_ratio: round2(snap.log_error_burst_ratio),
        });
    }

    let score = base.min(100.0);
    (score, reasons)
}

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;

    fn make_snap(error_rate: f64, log_err: u64, log_warn: u64) -> ServiceSignalSnapshot {
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
            error_rate_1h: error_rate,
            log_error_count_1h: log_err,
            log_warn_count_1h: log_warn,
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
    fn test_clean_service() {
        let snap = make_snap(0.0, 0, 0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 0.0);
        assert!(reasons.is_empty());
    }

    #[test]
    fn test_high_error_rate() {
        let snap = make_snap(0.25, 0, 0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 50.0);
        assert!(reasons.iter().any(|r| matches!(r, ReasonCode::ErrorRateElevated { .. })));
    }

    #[test]
    fn test_log_errors_only() {
        let snap = make_snap(0.0, 55, 0);
        let (s, _) = score(&snap);
        assert_eq!(s, 30.0);
    }

    #[test]
    fn test_warn_conservative() {
        // 150 warnings should only add 6 points
        let snap = make_snap(0.0, 0, 150);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 6.0, "150 warnings should score 6, got {s}");
        assert!(reasons.iter().any(|r| matches!(r, ReasonCode::LogWarningSurge { .. })));
    }

    #[test]
    fn test_warn_below_threshold() {
        // 40 warnings should add 0 points
        let snap = make_snap(0.0, 0, 40);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 0.0, "40 warnings should score 0, got {s}");
        assert!(reasons.is_empty());
    }
}
