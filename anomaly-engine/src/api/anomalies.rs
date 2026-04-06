use axum::{
    extract::{Query, State},
    Json,
};
use serde::{Deserialize, Serialize};

use crate::models::anomaly::AnomalySummary;
use crate::persistence::{db::Database, history, repository};

#[derive(Deserialize)]
pub struct ListParams {
    pub active_only: Option<bool>,
    pub limit: Option<i64>,
}

#[derive(Serialize)]
pub struct AnomalyListResponse {
    pub anomalies: Vec<repository::AnomalyRow>,
    pub count: usize,
    pub summary: AnomalySummary,
}

/// GET /api/v2/anomalies
pub async fn list_anomalies(
    State(db): State<Database>,
    Query(params): Query<ListParams>,
) -> Result<Json<AnomalyListResponse>, axum::http::StatusCode> {
    let active_only = params.active_only.unwrap_or(false);
    let limit = params.limit.unwrap_or(100);

    let anomalies = if active_only {
        repository::get_active_anomalies(&db.pool)
            .await
            .map_err(|e| {
                tracing::error!("DB error: {e}");
                axum::http::StatusCode::INTERNAL_SERVER_ERROR
            })?
    } else {
        repository::get_all_anomalies(&db.pool, limit)
            .await
            .map_err(|e| {
                tracing::error!("DB error: {e}");
                axum::http::StatusCode::INTERNAL_SERVER_ERROR
            })?
    };

    let count = anomalies.len();
    let summary = build_summary(&anomalies);

    Ok(Json(AnomalyListResponse {
        anomalies,
        count,
        summary,
    }))
}

#[derive(Serialize)]
pub struct HistoryResponse {
    pub history: Vec<history::HistoryRow>,
    pub count: usize,
}

/// GET /api/v2/anomalies/history
pub async fn list_history(
    State(db): State<Database>,
) -> Result<Json<HistoryResponse>, axum::http::StatusCode> {
    let rows = history::get_recent_history(&db.pool, 50)
        .await
        .map_err(|e| {
            tracing::error!("DB error: {e}");
            axum::http::StatusCode::INTERNAL_SERVER_ERROR
        })?;

    let count = rows.len();
    Ok(Json(HistoryResponse {
        history: rows,
        count,
    }))
}

fn build_summary(rows: &[repository::AnomalyRow]) -> AnomalySummary {
    use crate::models::anomaly::SeverityCounts;

    let active: Vec<_> = rows.iter().filter(|r| r.status == "active").collect();
    let total_active = active.len() as u32;

    let mut counts = SeverityCounts {
        normal: 0,
        watch: 0,
        degraded: 0,
        critical: 0,
        emergency: 0,
    };

    for row in &active {
        match row.severity.as_str() {
            "normal" => counts.normal += 1,
            "watch" => counts.watch += 1,
            "degraded" => counts.degraded += 1,
            "critical" => counts.critical += 1,
            "emergency" => counts.emergency += 1,
            _ => {}
        }
    }

    let max_score = active
        .iter()
        .map(|r| r.anomaly_score as f64)
        .fold(0.0_f64, f64::max);

    AnomalySummary {
        total_active,
        severity_counts: counts,
        max_score,
    }
}
