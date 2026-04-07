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
    let predicted_risk_level_str = output.predicted_risk_level.as_str();
    let prediction_confidence_str = output.prediction_confidence.as_str();
    let prediction_reason_codes_json =
        serde_json::to_value(&output.prediction_reason_codes).unwrap_or_default();

    sqlx::query(
        r#"
        INSERT INTO anomaly_engine_results_v1 (
            id, service_id, service_name, service_type, group_name, environment,
            anomaly_score, severity, confidence, confidence_label,
            category_scores, reason_codes, evidence_summary,
            status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
            baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio,
            trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations,
            predicted_risk_score, predicted_risk_level, predicted_horizon_minutes,
            prediction_confidence, prediction_reason_codes, prediction_summary
        ) VALUES (
            $1, $2, $3, $4, $5, $6,
            $7, $8, $9, $10,
            $11, $12, $13,
            $14, $15, $16, $17, $18,
            $19, $20, $21, $22,
            $23, $24, $25,
            $26, $27, $28, $29,
            $30, $31, $32,
            $33, $34, $35
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
            trace_p95_latency_ms = $26,
            trace_error_rate = $27,
            trace_bottleneck_score = $28,
            trace_slow_operations = $29,
            predicted_risk_score = $30,
            predicted_risk_level = $31,
            predicted_horizon_minutes = $32,
            prediction_confidence = $33,
            prediction_reason_codes = $34,
            prediction_summary = $35,
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
    .bind(output.trace_p95_latency_ms as f32)
    .bind(output.trace_error_rate as f32)
    .bind(output.trace_bottleneck_score as f32)
    .bind(output.trace_slow_operations as i32)
    .bind(output.predicted_risk_score as i16)
    .bind(predicted_risk_level_str)
    .bind(output.predicted_horizon_minutes.map(|v| v as i32))
    .bind(prediction_confidence_str)
    .bind(&prediction_reason_codes_json)
    .bind(&output.prediction_summary)
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
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio,
            trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations,
            predicted_risk_score, predicted_risk_level, predicted_horizon_minutes,
            prediction_confidence, prediction_reason_codes, prediction_summary
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
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio,
            trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations,
            predicted_risk_score, predicted_risk_level, predicted_horizon_minutes,
            prediction_confidence, prediction_reason_codes, prediction_summary
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
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio,
            trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations,
            predicted_risk_score, predicted_risk_level, predicted_horizon_minutes,
            prediction_confidence, prediction_reason_codes, prediction_summary
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
            latency_trend_slope, latency_trend_r2, log_error_burst_ratio,
            trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations,
            predicted_risk_score, predicted_risk_level, predicted_horizon_minutes,
            prediction_confidence, prediction_reason_codes, prediction_summary
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
    pub trace_p95_latency_ms: Option<f32>,
    pub trace_error_rate: Option<f32>,
    pub trace_bottleneck_score: Option<f32>,
    pub trace_slow_operations: Option<i32>,
    pub predicted_risk_score: Option<i16>,
    pub predicted_risk_level: Option<String>,
    pub predicted_horizon_minutes: Option<i32>,
    pub prediction_confidence: Option<String>,
    pub prediction_reason_codes: Option<serde_json::Value>,
    pub prediction_summary: Option<String>,
}

// ─── V1.6 LLM explanation support ───

const ANOMALY_ROW_COLUMNS: &str = r#"
    id, service_id, service_name, service_type, group_name, environment,
    anomaly_score, severity, confidence, confidence_label,
    category_scores, reason_codes, evidence_summary,
    status, fingerprint, first_seen_at, last_seen_at, occurrence_count,
    baseline_deviation_pct, triggered_categories_count, is_anomalous, evaluation_duration_ms,
    latency_trend_slope, latency_trend_r2, log_error_burst_ratio,
    trace_p95_latency_ms, trace_error_rate, trace_bottleneck_score, trace_slow_operations,
    predicted_risk_score, predicted_risk_level, predicted_horizon_minutes,
    prediction_confidence, prediction_reason_codes, prediction_summary
"#;

/// Fetch a single anomaly by UUID.
pub async fn get_anomaly_by_id(pool: &PgPool, id: Uuid) -> Result<Option<AnomalyRow>, sqlx::Error> {
    let query = format!(
        "SELECT {} FROM anomaly_engine_results_v1 WHERE id = $1",
        ANOMALY_ROW_COLUMNS
    );
    let row = sqlx::query_as::<_, AnomalyRow>(&query)
        .bind(id)
        .fetch_optional(pool)
        .await?;

    Ok(row)
}

/// Get a cached LLM explanation if the score hasn't changed and it's < 10 min old.
pub async fn get_cached_explanation(
    pool: &PgPool,
    anomaly_id: Uuid,
    current_score: i16,
) -> Result<Option<(serde_json::Value, String)>, sqlx::Error> {
    let row = sqlx::query(
        r#"
        SELECT explanation_json, model_used
        FROM anomaly_explanations_cache
        WHERE anomaly_id = $1
          AND anomaly_score_at_generation = $2
          AND generated_at > NOW() - INTERVAL '10 minutes'
        "#,
    )
    .bind(anomaly_id)
    .bind(current_score)
    .fetch_optional(pool)
    .await?;

    Ok(row.map(|r| {
        use sqlx::Row;
        let json: serde_json::Value = r.get("explanation_json");
        let model: String = r.get("model_used");
        (json, model)
    }))
}

/// Insert or update an LLM explanation in the cache.
pub async fn cache_explanation(
    pool: &PgPool,
    anomaly_id: Uuid,
    score: i16,
    explanation_json: &serde_json::Value,
    model: &str,
) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        INSERT INTO anomaly_explanations_cache
            (anomaly_id, anomaly_score_at_generation, explanation_json, model_used, generated_at)
        VALUES ($1, $2, $3, $4, NOW())
        ON CONFLICT (anomaly_id) DO UPDATE SET
            anomaly_score_at_generation = $2,
            explanation_json = $3,
            model_used = $4,
            generated_at = NOW()
        "#,
    )
    .bind(anomaly_id)
    .bind(score)
    .bind(explanation_json)
    .bind(model)
    .execute(pool)
    .await?;

    Ok(())
}
