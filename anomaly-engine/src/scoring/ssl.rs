use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;

/// SSL category scorer.
/// Weight: 0.15 of composite.
///
/// This is a **RISK SIGNAL**, not an operational anomaly.
/// It surfaces certificate expiry proximity as a forward-looking
/// risk indicator rather than current operational degradation.
///
/// Inputs: ssl_expiry_days
/// Score range: 0–100
pub fn score(snap: &ServiceSignalSnapshot) -> (f64, Vec<ReasonCode>) {
    let days = snap.ssl_expiry_days;
    let mut reasons = Vec::new();

    let base = if days <= 0.0 {
        reasons.push(ReasonCode::SslExpired);
        100.0
    } else if days <= 7.0 {
        reasons.push(ReasonCode::SslExpirySoon {
            days_remaining: round2(days),
        });
        90.0
    } else if days <= 14.0 {
        reasons.push(ReasonCode::SslExpirySoon {
            days_remaining: round2(days),
        });
        70.0
    } else if days <= 30.0 {
        reasons.push(ReasonCode::SslExpirySoon {
            days_remaining: round2(days),
        });
        40.0
    } else if days <= 60.0 {
        // Low risk — no reason code emitted, just a small score bump
        15.0
    } else {
        0.0
    };

    (base, reasons)
}

fn round2(v: f64) -> f64 {
    (v * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;

    fn make_snap(ssl_days: f64) -> ServiceSignalSnapshot {
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
            is_up: true,
            health_score: 97.0,
            consecutive_failures: 0,
            incidents_24h: 0,
            error_rate_1h: 0.0,
            log_error_count_1h: 0,
            log_warn_count_1h: 0,
            ssl_expiry_days: ssl_days,
            baseline_age_hours: 24.0,
            checks_in_last_1h: 60,
            signals_available: vec![],
        }
    }

    #[test]
    fn test_ssl_healthy() {
        let snap = make_snap(120.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 0.0);
        assert!(reasons.is_empty());
    }

    #[test]
    fn test_ssl_expired() {
        let snap = make_snap(-1.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 100.0);
        assert!(reasons.iter().any(|r| matches!(r, ReasonCode::SslExpired)));
    }

    #[test]
    fn test_ssl_7_days() {
        let snap = make_snap(5.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 90.0);
        assert!(reasons.iter().any(|r| matches!(r, ReasonCode::SslExpirySoon { .. })));
    }

    #[test]
    fn test_ssl_30_days() {
        let snap = make_snap(25.0);
        let (s, _) = score(&snap);
        assert_eq!(s, 40.0);
    }

    #[test]
    fn test_ssl_48_days() {
        // rhinometric-web has ~48 days — should be minor
        let snap = make_snap(48.0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 15.0);
        assert!(reasons.is_empty(), "48 days should not emit reason code");
    }
}
