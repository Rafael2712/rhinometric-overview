use chrono::{DateTime, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use crate::models::anomaly::AnomalyOutput;

/// Upsert an anomaly result into the database.
/// Uses fingerprint-based deduplication: if same service_id + fingerprint
/// exists, update the existing row (increment occurrence_count, update last_seen).
/// Otherwise insert new row.
pub async fn upsert_result(pool: &PgPool, output: &AnomalyOutput) -> Result<(), sqlx::Error> {
    let severity_str = output.severity.as_str();
    let confidence_label_str = output.confidence_label.as_str();
    let status_str = output.status.as_str();
    let reason_codes_json = serde_json::to_value(&output.reason_codes).unwrap_or_default();
    let category_scores_json = serde_json::to_value(&output.category_scores).unwrap_or_default();

    sqlx::query(
        r#"
        INSERT INTO anomaly_engine_results_v1 (
            id, service_id, service_name, service_type, group_name, environment,
            anomaly_score, severity, confidence, confidence_label,
            category_scores, reason_codes, evidence_summary,
            status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
            baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio
        ) VALUES (
            $1, $2, $3, $4, $5, $6,
            $7, $8, $9, $10,
            $11, $12, $13,
            $14, $15, $16, $17, $18,
            $19, $20, $21, $22,
            $23, $24, $25
        )
        ON CONFLICT (service_id, fingerprint) WHERE status = 'active'
        DO UPDATE SET
            anomaly_score = $7,
            severity = $8,
            confidence = $9,
            confidence_label = $10,
            category_scores = $11,
            reason_codes = $12,
            evidence_summary = $13,
            last_seen_at = $17,
            occurrence_count = anomaly_engine_results_v1.occurrence_count + 1,
            baseline_deviation_pct = $19,
            triggered_categories_count = $20,
            is_anomalous = $21,
            evaluation_duration_ms = $22,
            latency_trend_slope = $23,
            latency_trend_r2 = $24,
            log_error_burst_ratio = $25,
            updated_at = now()
        "#,
    )
    .bind(output.id)
    .bind(output.service_id as i32)
    .bind(&output.service_name)
    .bind(&output.service_type)
    .bind(&output.group_name)
    .bind(&output.environment)
    .bind(output.score as i16)
    .bind(severity_str)
    .bind(output.confidence as f32)
    .bind(confidence_label_str)
    .bind(&category_scores_json)
    .bind(&reason_codes_json)
    .bind(&output.evidence_summary)
    .bind(status_str)
    .bind(&output.fingerprint)
    .bind(output.first_seen)
    .bind(output.last_seen)
    .bind(output.occurrence_count as i32)
    .bind(output.baseline_deviation_pct as f32)
    .bind(output.triggered_categories_count)
    .bind(output.is_anomalous)
    .bind(output.evaluation_duration_ms)
    .bind(output.latency_trend_slope as f32)
    .bind(output.latency_trend_r2 as f32)
    .bind(output.log_error_burst_ratio as f32)
    .execute(pool)
    .await?;

    Ok(())
}

/// Mark stale anomalies as resolved.
/// If a service_id had an active anomaly but wasn't re-evaluated 
/// with the same fingerprint, it means the anomaly resolved.
pub async fn resolve_stale(
    pool: &PgPool,
    active_service_ids: &[i64],
    active_fingerprints: &[String],
    cutoff: DateTime<Utc>,
) -> Result<u64, sqlx::Error> {
    let result = sqlx::query(
        r#"
        UPDATE anomaly_engine_results_v1
        SET status = 'resolved', last_seen_at = $1, updated_at = now()
        WHERE status = 'active'
          AND (
            service_id != ALL($2::bigint[])
            OR fingerprint != ALL($3::text[])
          )
          AND last_seen_at < $1
        "#,
    )
    .bind(cutoff)
    .bind(active_service_ids)
    .bind(active_fingerprints)
    .execute(pool)
    .await?;

    Ok(result.rows_affected())
}

/// Fetch all active anomalies, ordered by score descending.
pub async fn get_active_anomalies(pool: &PgPool) -> Result<Vec<AnomalyRow>, sqlx::Error> {
    let rows = sqlx::query_as::<_, AnomalyRow>(
        r#"
        SELECT
            id, service_id, service_name, service_type, group_name, environment,
            anomaly_score, severity, confidence, confidence_label,
            category_scores, reason_codes, evidence_summary,
            status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
            baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio
        FROM anomaly_engine_results_v1
        WHERE status = 'active'
        ORDER BY anomaly_score DESC
        "#,
    )
    .fetch_all(pool)
    .await?;

    Ok(rows)
}

/// Fetch all anomalies (active + recently resolved), ordered by score descending.
pub async fn get_all_anomalies(pool: &PgPool, limit: i64) -> Result<Vec<AnomalyRow>, sqlx::Error> {
    let rows = sqlx::query_as::<_, AnomalyRow>(
        r#"
        SELECT
            id, service_id, service_name, service_type, group_name, environment,
            anomaly_score, severity, confidence, confidence_label,
            category_scores, reason_codes, evidence_summary,
            status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
            baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio
        FROM anomaly_engine_results_v1
        ORDER BY
            CASE WHEN status = 'active' THEN 0 ELSE 1 END,
            anomaly_score DESC
        LIMIT $1
        "#,
    )
    .bind(limit)
    .fetch_all(pool)
    .await?;

    Ok(rows)
}

/// Fetch deduplicated active anomalies — one row per service_id, highest score wins.
pub async fn get_active_deduplicated(pool: &PgPool, limit: i64) -> Result<Vec<AnomalyRow>, sqlx::Error> {
    let rows = sqlx::query_as::<_, AnomalyRow>(
        r#"
        SELECT DISTINCT ON (service_id)
            id, service_id, service_name, service_type, group_name, environment,
            anomaly_score, severity, confidence, confidence_label,
            category_scores, reason_codes, evidence_summary,
            status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
            baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio
        FROM anomaly_engine_results_v1
        WHERE status = 'active'
        ORDER BY service_id, anomaly_score DESC, last_seen_at DESC
        "#,
    )
    .fetch_all(pool)
    .await?;

    // Re-sort by score descending after DISTINCT ON (which requires service_id ordering first)
    let mut rows = rows;
    rows.sort_by(|a, b| b.anomaly_score.cmp(&a.anomaly_score));
    if rows.len() > limit as usize {
        rows.truncate(limit as usize);
    }
    Ok(rows)
}

/// Fetch recently resolved anomalies (for history view).
pub async fn get_resolved_recent(pool: &PgPool, limit: i64) -> Result<Vec<AnomalyRow>, sqlx::Error> {
    let rows = sqlx::query_as::<_, AnomalyRow>(
        r#"
        SELECT
            id, service_id, service_name, service_type, group_name, environment,
            anomaly_score, severity, confidence, confidence_label,
            category_scores, reason_codes, evidence_summary,
            status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
            baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio
        FROM anomaly_engine_results_v1
        WHERE status = 'resolved'
        ORDER BY last_seen_at DESC
        LIMIT $1
        "#,
    )
    .bind(limit)
    .fetch_all(pool)
    .await?;

    Ok(rows)
}

/// Raw row from the database.
#[derive(Debug, sqlx::FromRow, serde::Serialize)]
pub struct AnomalyRow {
    pub id: Uuid,
    pub service_id: i32,
    pub service_name: String,
    pub service_type: Option<String>,
    pub group_name: Option<String>,
    pub environment: Option<String>,
    pub anomaly_score: i16,
    pub severity: String,
    pub confidence: f32,
    pub confidence_label: String,
    pub category_scores: serde_json::Value,
    pub reason_codes: serde_json::Value,
    pub evidence_summary: String,
    pub status: String,
    pub fingerprint: String,
    pub first_seen_at: DateTime<Utc>,
    pub last_seen_at: DateTime<Utc>,
    pub occurrence_count: i32,
    pub baseline_deviation_pct: Option<f32>,
    pub triggered_categories_count: Option<i16>,
    pub is_anomalous: Option<bool>,
    pub evaluation_duration_ms: Option<i32>,
    pub latency_trend_slope: Option<f32>,
    pub latency_trend_r2: Option<f32>,
    pub log_error_burst_ratio: Option<f32>,
}
