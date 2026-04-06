use axum::{routing::get, Router};
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

use crate::persistence::db::Database;

/// Build the Axum router with all routes.
pub fn build_router(db: Database) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/health", get(crate::api::health::health))
        .route("/api/v2/anomalies", get(crate::api::anomalies::list_anomalies))
        .route(
            "/api/v2/anomalies/history",
            get(crate::api::anomalies::list_history),
        )
        .route("/metrics", get(crate::api::metrics::metrics))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(db)
}
