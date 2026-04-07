use axum::{
    extract::{Query, State},
    Json,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::persistence::repository;
use crate::server::AppState;

/// Query params for the batch AI context endpoint.
#[derive(Deserialize)]
pub struct AlertContextParams {
    /// Comma-separated service names to look up.
    pub service_names: String,
}

/// Compact AI context returned per service.
#[derive(Debug, Serialize, Clone)]
pub struct ServiceAiContext {
    pub anomaly_id: String,
    pub anomaly_score: i16,
    pub severity: String,
    pub status: String,
    pub confidence: f32,
    pub confidence_label: String,
    pub evidence_summary: String,
    pub predicted_risk_score: Option<i16>,
    pub predicted_risk_level: Option<String>,
    pub predicted_horizon_minutes: Option<i32>,
    pub prediction_confidence: Option<String>,
    pub prediction_summary: Option<String>,
    pub explanation_summary: Option<String>,
    pub first_seen_at: String,
    pub last_seen_at: String,
}

/// Response wrapper.
#[derive(Serialize)]
pub struct AlertContextResponse {
    pub contexts: HashMap<String, ServiceAiContext>,
    pub count: usize,
}

/// GET /api/v2/alerts/ai-context?service_names=svc1,svc2
///
/// Returns the most recent anomaly context + cached LLM explanation summary
/// for each requested service. Prefers active anomalies; falls back to most
/// recently resolved. Does NOT trigger LLM calls — only reads the cache.
pub async fn get_alert_ai_context(
    State(state): State<AppState>,
    Query(params): Query<AlertContextParams>,
) -> Result<Json<AlertContextResponse>, axum::http::StatusCode> {
    let names: Vec<String> = params
        .service_names
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    if names.is_empty() {
        return Ok(Json(AlertContextResponse {
            contexts: HashMap::new(),
            count: 0,
        }));
    }

    // Batch-fetch the most recent anomaly per requested service
    let rows = repository::get_latest_anomalies_for_services(&state.db.pool, &names)
        .await
        .map_err(|e| {
            tracing::error!("DB error fetching alert AI context: {e}");
            axum::http::StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // Collect anomaly IDs so we can batch-fetch explanation cache
    let anomaly_ids: Vec<uuid::Uuid> = rows.iter().map(|r| r.id).collect();

    let explanations = repository::get_cached_explanations_batch(&state.db.pool, &anomaly_ids)
        .await
        .map_err(|e| {
            tracing::error!("DB error fetching explanation cache: {e}");
            axum::http::StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // Build the response map
    let mut contexts = HashMap::new();
    for row in &rows {
        let explanation_summary = explanations
            .get(&row.id)
            .and_then(|json| json.get("summary").and_then(|v| v.as_str()))
            .map(|s| s.to_string());

        contexts.insert(
            row.service_name.clone(),
            ServiceAiContext {
                anomaly_id: row.id.to_string(),
                anomaly_score: row.anomaly_score,
                severity: row.severity.clone(),
                status: row.status.clone(),
                confidence: row.confidence,
                confidence_label: row.confidence_label.clone(),
                evidence_summary: row.evidence_summary.clone(),
                predicted_risk_score: row.predicted_risk_score,
                predicted_risk_level: row.predicted_risk_level.clone(),
                predicted_horizon_minutes: row.predicted_horizon_minutes,
                prediction_confidence: row.prediction_confidence.clone(),
                prediction_summary: row.prediction_summary.clone(),
                explanation_summary,
                first_seen_at: row.first_seen_at.to_rfc3339(),
                last_seen_at: row.last_seen_at.to_rfc3339(),
            },
        );
    }

    let count = contexts.len();
    Ok(Json(AlertContextResponse { contexts, count }))
}
