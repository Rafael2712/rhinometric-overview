use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;

/// Trace-based anomaly scoring (V1.4).
///
/// Signals consumed:
///   - trace_bottleneck_score  (0.0–1.0, critical-path dominance)
///   - trace_error_rate        (0.0–1.0, error spans / total spans)
///   - trace_slow_operations   (count of slow ops)
///   - trace_p95_latency_ms    (p95 trace duration, used for latency amplification)
///
/// Score range: 0–100, clamped.
pub fn score(snap: &ServiceSignalSnapshot) -> (f64, Vec<ReasonCode>) {
    let mut s = 0.0_f64;
    let mut reasons = Vec::new();

    // ── Bottleneck dominance ──
    let bn = snap.trace_bottleneck_score;
    if bn > 0.7 {
        s += 40.0;
        reasons.push(ReasonCode::TraceBottleneck {
            score: bn,
            threshold: 0.7,
        });
    } else if bn > 0.5 {
        s += 25.0;
        reasons.push(ReasonCode::TraceBottleneck {
            score: bn,
            threshold: 0.5,
        });
    } else if bn > 0.3 {
        s += 10.0;
        reasons.push(ReasonCode::TraceBottleneck {
            score: bn,
            threshold: 0.3,
        });
    }

    // ── Trace error rate ──
    let er = snap.trace_error_rate;
    if er > 0.15 {
        s += 30.0;
        reasons.push(ReasonCode::TraceErrorRate {
            rate: er,
            threshold: 0.15,
        });
    } else if er > 0.05 {
        s += 15.0;
        reasons.push(ReasonCode::TraceErrorRate {
            rate: er,
            threshold: 0.05,
        });
    }

    // ── Slow operations ──
    let slow = snap.trace_slow_operations;
    if slow >= 5 {
        s += 20.0;
        reasons.push(ReasonCode::TraceSlowOperations {
            count: slow,
            threshold: 5,
        });
    } else if slow >= 2 {
        s += 10.0;
        reasons.push(ReasonCode::TraceSlowOperations {
            count: slow,
            threshold: 2,
        });
    }

    // ── Latency amplification ──
    // If trace P95 > 2× metric baseline, extra penalty.
    if snap.latency_baseline_ms > 0.0
        && snap.trace_p95_latency_ms > snap.latency_baseline_ms * 2.0
    {
        s += 10.0;
    }

    (s.clamp(0.0, 100.0), reasons)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;

    fn make_snap(
        bottleneck: f64,
        error_rate: f64,
        slow_ops: u32,
        trace_p95: f64,
        baseline: f64,
    ) -> ServiceSignalSnapshot {
        ServiceSignalSnapshot {
            service_name: "test".into(),
            service_id: 1,
            service_type: "http".into(),
            group_name: "Default".into(),
            environment: "test".into(),
            timestamp_ms: 0,
            check_interval_seconds: 60,
            latency_current_ms: 100.0,
            latency_baseline_ms: baseline,
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
            trace_p95_latency_ms: trace_p95,
            trace_error_rate: error_rate,
            trace_bottleneck_score: bottleneck,
            trace_slow_operations: slow_ops,
            baseline_age_hours: 24.0,
            checks_in_last_1h: 60,
            signals_available: vec![],
        }
    }

    #[test]
    fn test_no_trace_signals() {
        let snap = make_snap(0.0, 0.0, 0, 0.0, 100.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 0.0);
        assert!(reasons.is_empty());
    }

    #[test]
    fn test_high_bottleneck() {
        let snap = make_snap(0.8, 0.0, 0, 0.0, 100.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 40.0);
        assert_eq!(reasons.len(), 1);
    }

    #[test]
    fn test_medium_bottleneck() {
        let snap = make_snap(0.6, 0.0, 0, 0.0, 100.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 25.0);
    }

    #[test]
    fn test_error_rate_high() {
        let snap = make_snap(0.0, 0.20, 0, 0.0, 100.0);
        let (s, _) = score(&snap);
        assert_eq!(s, 30.0);
    }

    #[test]
    fn test_slow_ops() {
        let snap = make_snap(0.0, 0.0, 5, 0.0, 100.0);
        let (s, _) = score(&snap);
        assert_eq!(s, 20.0);
    }

    #[test]
    fn test_latency_amplification() {
        // trace P95 = 300, baseline = 100 → 300 > 200 → +10
        let snap = make_snap(0.0, 0.0, 0, 300.0, 100.0);
        let (s, _) = score(&snap);
        assert_eq!(s, 10.0);
    }

    #[test]
    fn test_combined_clamped() {
        // bottleneck 0.8→40 + error 0.20→30 + slow 5→20 + amplification→10 = 100 (clamped)
        let snap = make_snap(0.8, 0.20, 5, 300.0, 100.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 100.0);
        assert_eq!(reasons.len(), 3);
    }
}
