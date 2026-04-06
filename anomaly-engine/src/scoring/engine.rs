use chrono::Utc;
use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::models::anomaly::{AnomalyOutput, AnomalyStatus, CategoryScores};
use crate::models::severity::{ConfidenceLabel, Severity};
use crate::models::snapshot::ServiceSignalSnapshot;
use crate::scoring::{composite, confidence, evidence};

/// Run the full scoring pipeline for a single service snapshot.
///
/// Pipeline: categorise → composite → confidence → severity → evidence → output
pub fn evaluate(snap: &ServiceSignalSnapshot) -> AnomalyOutput {
    // 1. Composite scoring (calls all 4 category scorers)
    let comp = composite::score(snap);

    // 2. Confidence
    let cat_scores = [
        comp.latency_score,
        comp.availability_score,
        comp.error_score,
        comp.ssl_score,
    ];
    let conf = confidence::compute(snap, &cat_scores);

    // 3. Severity from composite score
    let severity = Severity::from_score(comp.score);

    // 4. Evidence summary
    let evidence_summary = evidence::build(comp.score, &severity, &comp.reason_codes);

    // 5. Deterministic fingerprint: sha256(service_id + sorted reason code labels)
    let fingerprint = compute_fingerprint(snap.service_id, &comp.reason_codes);

    // 6. Status
    let status = if comp.score > 15.0 {
        AnomalyStatus::Active
    } else {
        AnomalyStatus::Resolved
    };

    // 7. Validation fields (V1.1)
    let baseline_deviation_pct = if snap.latency_baseline_ms > 0.0 {
        ((snap.latency_current_ms - snap.latency_baseline_ms) / snap.latency_baseline_ms) * 100.0
    } else {
        0.0
    };

    let triggered_categories_count = [
        comp.latency_score,
        comp.availability_score,
        comp.error_score,
        comp.ssl_score,
    ]
    .iter()
    .filter(|&&s| s > 15.0)
    .count() as i16;

    let is_anomalous = comp.score > 35.0;

    let now = Utc::now();

    AnomalyOutput {
        id: Uuid::new_v4(),
        service_id: snap.service_id,
        service_name: snap.service_name.clone(),
        service_type: snap.service_type.clone(),
        group_name: snap.group_name.clone(),
        environment: snap.environment.clone(),
        score: comp.score,
        severity,
        confidence: conf,
        confidence_label: ConfidenceLabel::from_score(conf),
        category_scores: CategoryScores {
            latency: comp.latency_score,
            availability: comp.availability_score,
            error: comp.error_score,
            ssl: comp.ssl_score,
        },
        reason_codes: comp.reason_codes,
        evidence_summary,
        status,
        fingerprint,
        evaluated_at: now,
        first_seen: now,
        last_seen: now,
        occurrence_count: 1,
        baseline_deviation_pct,
        triggered_categories_count,
        is_anomalous,
        evaluation_duration_ms: 0, // set by worker after timing
    }
}

/// Deterministic fingerprint for deduplication.
/// Same service_id + same set of reason code types → same fingerprint.
fn compute_fingerprint(
    service_id: i64,
    reasons: &[crate::models::reason_code::ReasonCode],
) -> String {
    let mut hasher = Sha256::new();
    hasher.update(service_id.to_le_bytes());

    let mut labels: Vec<String> = reasons.iter().map(|r| r.label()).collect();
    labels.sort();
    for label in &labels {
        hasher.update(label.as_bytes());
    }

    let hash = hasher.finalize();
    hex::encode(&hash[..16]) // 32-char hex (128 bits — plenty for fingerprint)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::snapshot::ServiceSignalSnapshot;

    fn base_snap() -> ServiceSignalSnapshot {
        ServiceSignalSnapshot {
            service_name: "rhinometric-web".into(),
            service_id: 130,
            service_type: "http".into(),
            group_name: "Production".into(),
            environment: "production".into(),
            timestamp_ms: 1700000000000,
            check_interval_seconds: 60,
            latency_current_ms: 200.0,
            latency_baseline_ms: 200.0,
            latency_p95_ms: 350.0,
            is_up: true,
            health_score: 97.1,
            consecutive_failures: 0,
            incidents_24h: 0,
            error_rate_1h: 0.0,
            log_error_count_1h: 0,
            log_warn_count_1h: 0,
            ssl_expiry_days: 48.1,
            baseline_age_hours: 24.0,
            checks_in_last_1h: 60,
            signals_available: vec![
                "latency_current_ms".into(),
                "health_score".into(),
                "ssl_expiry_days".into(),
            ],
        }
    }

    #[test]
    fn test_healthy_service() {
        let snap = base_snap();
        let output = evaluate(&snap);
        assert!(output.score <= 15.0, "Healthy service score: {}", output.score);
        assert!(matches!(output.severity, Severity::Normal));
        assert!(matches!(output.status, AnomalyStatus::Resolved));
    }

    #[test]
    fn test_degraded_service() {
        let mut snap = base_snap();
        snap.latency_current_ms = 800.0;     // 300% above baseline
        snap.health_score = 60.0;
        snap.error_rate_1h = 0.08;
        snap.log_error_count_1h = 10;
        let output = evaluate(&snap);
        assert!(output.score > 15.0, "Degraded should score high: {}", output.score);
        assert!(!output.reason_codes.is_empty());
        assert!(matches!(output.status, AnomalyStatus::Active));
    }

    #[test]
    fn test_critical_service() {
        let mut snap = base_snap();
        snap.is_up = false;
        snap.health_score = 20.0;
        snap.consecutive_failures = 10;
        snap.latency_current_ms = 2000.0;
        snap.error_rate_1h = 0.30;
        snap.incidents_24h = 5;
        let output = evaluate(&snap);
        assert!(output.score > 60.0, "Critical should be >60: {}", output.score);
    }

    #[test]
    fn test_fingerprint_deterministic() {
        let snap = base_snap();
        let o1 = evaluate(&snap);
        let o2 = evaluate(&snap);
        assert_eq!(o1.fingerprint, o2.fingerprint, "Same input → same fingerprint");
    }
}
