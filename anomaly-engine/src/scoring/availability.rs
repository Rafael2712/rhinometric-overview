use crate::models::reason_code::ReasonCode;
use crate::models::snapshot::ServiceSignalSnapshot;

/// Availability category scorer.
/// Weight: 0.30 of composite.
///
/// Inputs: is_up, health_score, consecutive_failures, incidents_24h
/// Score range: 0–100
pub fn score(snap: &ServiceSignalSnapshot) -> (f64, Vec<ReasonCode>) {
    let mut base: f64 = 0.0;
    let mut reasons = Vec::new();

    // Health score component (0–40)
    if snap.health_score < 50.0 {
        base += 40.0;
        reasons.push(ReasonCode::HealthScoreLow {
            score: round2(snap.health_score),
            baseline: 85.0, // Expected healthy baseline
        });
    } else if snap.health_score < 70.0 {
        base += 25.0;
        reasons.push(ReasonCode::HealthScoreLow {
            score: round2(snap.health_score),
            baseline: 85.0,
        });
    } else if snap.health_score < 85.0 {
        base += 10.0;
    }

    // Down status (0–30)
    if !snap.is_up {
        base += 30.0;
        reasons.push(ReasonCode::ServiceDown {
            consecutive_failures: snap.consecutive_failures,
        });
    }

    // Consecutive failures (0–20)
    if snap.consecutive_failures >= 5 {
        base += 20.0;
        reasons.push(ReasonCode::FailureStreak {
            count: snap.consecutive_failures,
        });
    } else if snap.consecutive_failures >= 3 {
        base += 12.0;
        reasons.push(ReasonCode::FailureStreak {
            count: snap.consecutive_failures,
        });
    } else if snap.consecutive_failures >= 1 {
        base += 5.0;
    }

    // Recent incidents (0–10)
    if snap.incidents_24h >= 3 {
        base += 10.0;
        reasons.push(ReasonCode::UptimeDegraded {
            incidents_24h: snap.incidents_24h,
        });
    } else if snap.incidents_24h >= 1 {
        base += 5.0;
        reasons.push(ReasonCode::UptimeDegraded {
            incidents_24h: snap.incidents_24h,
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

    fn make_snap(is_up: bool, health: f64, failures: u32, incidents: u32) -> ServiceSignalSnapshot {
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
            is_up,
            health_score: health,
            consecutive_failures: failures,
            incidents_24h: incidents,
            error_rate_1h: 0.0,
            log_error_count_1h: 0,
            log_warn_count_1h: 0,
            ssl_expiry_days: 365.0,
            baseline_age_hours: 24.0,
            checks_in_last_1h: 60,
            signals_available: vec![],
        }
    }

    #[test]
    fn test_healthy_service() {
        let snap = make_snap(true, 97.0, 0, 0);
        let (s, reasons) = score(&snap);
        assert_eq!(s, 0.0);
        assert!(reasons.is_empty());
    }

    #[test]
    fn test_service_down() {
        let snap = make_snap(false, 30.0, 5, 1);
        let (s, reasons) = score(&snap);
        assert!(s >= 90.0, "Down service should score very high, got {s}");
        assert!(reasons.iter().any(|r| matches!(r, ReasonCode::ServiceDown { .. })));
    }

    #[test]
    fn test_degraded_health() {
        let snap = make_snap(true, 65.0, 0, 0);
        let (s, _) = score(&snap);
        assert!(s >= 20.0 && s <= 40.0, "Degraded health score: {s}");
    }
}
