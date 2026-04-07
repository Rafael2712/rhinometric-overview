use chrono::{DateTime, Utc};
use sqlx::PgPool;

/// Record a scoring cycle in the history table for audit/debugging.
pub async fn record_cycle(
    pool: &PgPool,
    services_evaluated: i32,
    anomalies_detected: i32,
    max_score: f64,
    cycle_duration_ms: i64,
    warnings: Option<String>,
) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        INSERT INTO anomaly_engine_history_v1 (
            cycle_time, services_evaluated, anomalies_detected,
            max_score, cycle_duration_ms, warnings
        ) VALUES ($1, $2, $3, $4, $5, $6)
        "#,
    )
    .bind(Utc::now())
    .bind(services_evaluated)
    .bind(anomalies_detected)
    .bind(max_score)
    .bind(cycle_duration_ms)
    .bind(warnings)
    .execute(pool)
    .await?;

    Ok(())
}

/// Get last N history entries for observability.
pub async fn get_recent_history(
    pool: &PgPool,
    limit: i64,
) -> Result<Vec<HistoryRow>, sqlx::Error> {
    let rows = sqlx::query_as::<_, HistoryRow>(
        r#"
        SELECT id, cycle_time, services_evaluated, anomalies_detected,
               max_score, cycle_duration_ms, warnings, created_at
        FROM anomaly_engine_history_v1
        ORDER BY cycle_time DESC
        LIMIT $1
        "#,
    )
    .bind(limit)
    .fetch_all(pool)
    .await?;

    Ok(rows)
}

#[derive(Debug, sqlx::FromRow, serde::Serialize)]
pub struct HistoryRow {
    pub id: i64,
    pub cycle_time: DateTime<Utc>,
    pub services_evaluated: i32,
    pub anomalies_detected: i32,
    pub max_score: f64,
    pub cycle_duration_ms: i64,
    pub warnings: Option<String>,
    pub created_at: DateTime<Utc>,
}
