use tracing::info;

mod api;
mod client;
mod config;
mod models;
mod persistence;
mod scoring;
mod server;
mod worker;

use client::backend::BackendClient;
use config::AppConfig;
use persistence::db::Database;

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into()),
        )
        .json()
        .init();

    info!("Rhinometric Anomaly Engine V1 starting...");

    let config = AppConfig::from_env();
    info!(
        listen = %config.listen_addr,
        backend = %config.backend_url,
        interval = config.evaluation_interval_s,
        "Configuration loaded"
    );

    // Initialize database
    let db = Database::connect(&config.database_url)
        .await
        .expect("Failed to connect to PostgreSQL");
    info!("PostgreSQL connected");

    // HTTP client for snapshot fetching
    let backend_client = BackendClient::new(config.snapshots_url());

    // Start worker loop in background
    let worker_db = db.clone();
    let worker_client = backend_client.clone();
    let interval = config.evaluation_interval_s;
    tokio::spawn(async move {
        worker::run(worker_db, worker_client, interval).await;
    });

    // Build and start HTTP server (blocks)
    let router = server::build_router(db);
    let listener = tokio::net::TcpListener::bind(&config.listen_addr)
        .await
        .expect("Failed to bind listener");

    info!("HTTP server listening on {}", config.listen_addr);
    axum::serve(listener, router)
        .await
        .expect("Server error");
}
