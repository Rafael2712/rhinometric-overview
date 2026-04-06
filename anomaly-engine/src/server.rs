use axum::{routing::get, Router};
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

use crate::persistence::db::Database;

/// Shared app state for routes that need extra config.
#[derive(Clone)]
pub struct AppState {
    pub db: Database,
    pub python_anomaly_url: String,
}

/// Build the Axum router with all routes.
pub fn build_router(db: Database, python_anomaly_url: String) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let state = AppState {
        db: db.clone(),
        python_anomaly_url,
    };

    Router::new()
        .route("/health", get(crate::api::health::health))
        .route("/api/v2/anomalies", get(crate::api::anomalies::list_anomalies))
        .route(
            "/api/v2/anomalies/active",
            get(crate::api::anomalies::list_active),
        )
        .route(
            "/api/v2/anomalies/resolved",
            get(crate::api::anomalies::list_resolved),
        )
        .route(
            "/api/v2/anomalies/history",
            get(crate::api::anomalies::list_history),
        )
        .route(
            "/api/v2/anomalies/validation-summary",
            get(crate::api::validation::validation_summary),
        )
        .route(
            "/api/v2/anomalies/compare-python",
            get(crate::api::validation::compare_python),
        )
        .route("/metrics", get(crate::api::metrics::metrics))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
