use crate::models::reason_code::ReasonCode;
use crate::models::severity::Severity;

/// Build a human-readable evidence summary from reason codes and score.
///
/// Example output:
///   "Service Down (5 consecutive failures) · Latency Baseline Breach (+182% vs baseline) · Score 72/100 Critical"
pub fn build(score: f64, severity: &Severity, reasons: &[ReasonCode]) -> String {
    if reasons.is_empty() {
        return format!("No anomalies detected · Score {}/100 {}", score as u32, severity.as_str());
    }

    let mut parts: Vec<String> = reasons
        .iter()
        .take(4) // Max 4 reason labels to keep it readable
        .map(|r| r.label())
        .collect();

    parts.push(format!("Score {}/100 {}", score as u32, severity.as_str()));

    parts.join(" · ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_no_anomalies() {
        let result = build(5.0, &Severity::Normal, &[]);
        assert!(result.contains("No anomalies detected"));
    }

    #[test]
    fn test_single_reason() {
        let reasons = vec![ReasonCode::ServiceDown {
            consecutive_failures: 3,
        }];
        let result = build(72.0, &Severity::Critical, &reasons);
        assert!(result.contains("Service Down"));
        assert!(result.contains("Score 72/100 critical"));
    }

    #[test]
    fn test_multiple_reasons_capped() {
        let reasons = vec![
            ReasonCode::ServiceDown { consecutive_failures: 5 },
            ReasonCode::LatencyBaselineBreach { deviation_pct: 182.0, baseline_ms: 200.0 },
            ReasonCode::ErrorRateElevated { rate: 0.15, threshold: 0.05 },
            ReasonCode::LogErrorSurge { count: 42, window: "1h".into() },
            ReasonCode::SslExpirySoon { days_remaining: 7.0 }, // 5th — should be omitted
        ];
        let result = build(85.0, &Severity::Emergency, &reasons);
        // Should contain first 4 but not the 5th
        assert!(result.contains("Service Down"));
        assert!(result.contains("Score 85/100 emergency"));
        assert!(!result.contains("SSL"), "5th reason should be truncated");
    }
}
