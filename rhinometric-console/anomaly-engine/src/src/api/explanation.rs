use axum::{
    extract::{Path, State},
    Json,
};
use uuid::Uuid;

use crate::llm::explainer::{self, ExplanationApiResponse};
use crate::persistence::repository;
use crate::server::AppState;

/// GET /api/v2/anomalies/:id/explanation
///
/// Returns a deterministic LLM-generated explanation for the given anomaly.
/// Caches results in `anomaly_explanations_cache` — reuses cache if the
/// anomaly score hasn't changed and the entry is < 10 minutes old.
pub async fn get_explanation(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<ExplanationApiResponse>, (axum::http::StatusCode, String)> {
    // 1. Fetch anomaly by ID
    let row = repository::get_anomaly_by_id(&state.db.pool, id)
        .await
        .map_err(|e| {
            tracing::error!("DB error fetching anomaly {id}: {e}");
            (
                axum::http::StatusCode::INTERNAL_SERVER_ERROR,
                format!("Database error: {e}"),
            )
        })?
        .ok_or_else(|| {
            tracing::warn!("Anomaly {id} not found");
            (
                axum::http::StatusCode::NOT_FOUND,
                format!("Anomaly {id} not found"),
            )
        })?;

    // 2. Check cache (same score + < 10 min old)
    if let Ok(Some((explanation_json, model))) =
        repository::get_cached_explanation(&state.db.pool, id, row.anomaly_score).await
    {
        if let Ok(explanation) = serde_json::from_value(explanation_json) {
            tracing::debug!("Returning cached explanation for {id}");
            return Ok(Json(ExplanationApiResponse {
                anomaly_id: id,
                service_name: row.service_name,
                explanation,
                model,
                cached: true,
            }));
        }
    }

    // 3. Validate OpenAI key is configured
    let api_key = &state.openai_api_key;
    if api_key.is_empty() {
        tracing::error!("OPENAI_API_KEY not configured");
        return Err((
            axum::http::StatusCode::SERVICE_UNAVAILABLE,
            "LLM explanation service not configured".to_string(),
        ));
    }

    // 4. Generate explanation via LLM
    let model = &state.openai_model;
    let client = reqwest::Client::new();

    tracing::info!(
        anomaly_id = %id,
        service = %row.service_name,
        score = row.anomaly_score,
        "Generating LLM explanation"
    );

    let explanation = explainer::generate_explanation(&client, api_key, model, &row)
        .await
        .map_err(|e| {
            tracing::error!("LLM explanation failed for {id}: {e}");
            (
                axum::http::StatusCode::INTERNAL_SERVER_ERROR,
                format!("LLM generation failed: {e}"),
            )
        })?;

    // 5. Cache the result
    let explanation_json = serde_json::to_value(&explanation).unwrap_or_default();
    if let Err(e) = repository::cache_explanation(
        &state.db.pool,
        id,
        row.anomaly_score,
        &explanation_json,
        model,
    )
    .await
    {
        tracing::warn!("Failed to cache explanation for {id}: {e}");
    }

    tracing::info!(
        anomaly_id = %id,
        model = %model,
        "LLM explanation generated successfully"
    );

    Ok(Json(ExplanationApiResponse {
        anomaly_id: id,
        service_name: row.service_name,
        explanation,
        model: model.clone(),
        cached: false,
    }))
}
