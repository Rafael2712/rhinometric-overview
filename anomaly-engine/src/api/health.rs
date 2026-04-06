use axum::{extract::State, Json};
use serde::Serialize;

use crate::persistence::db::Database;

#[derive(Serialize)]
pub struct HealthResponse {
    pub status: &'static str,
    pub engine: &'static str,
    pub version: &'static str,
    pub database: &'static str,
}

/// GET /health
pub async fn health(State(db): State<Database>) -> Json<HealthResponse> {
    let db_ok = db.is_healthy().await;

    Json(HealthResponse {
        status: if db_ok { "healthy" } else { "degraded" },
        engine: "rhinometric-anomaly-engine-v1",
        version: env!("CARGO_PKG_VERSION"),
        database: if db_ok { "connected" } else { "unreachable" },
    })
}
