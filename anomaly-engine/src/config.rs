/// Application configuration loaded from environment variables.
#[derive(Debug, Clone)]
pub struct AppConfig {
    /// Backend URL for fetching signal snapshots
    pub backend_url: String,
    /// PostgreSQL connection string
    pub database_url: String,
    /// Evaluation interval in seconds
    pub evaluation_interval_s: u64,
    /// HTTP listen address
    pub listen_addr: String,
}

impl AppConfig {
    pub fn from_env() -> Self {
        Self {
            backend_url: std::env::var("BACKEND_URL")
                .unwrap_or_else(|_| "http://rhinometric-console-backend:8105".into()),
            database_url: std::env::var("DATABASE_URL").unwrap_or_else(|_| {
                "postgresql://rhinometric:rhinometric@postgres:5432/rhinometric".into()
            }),
            evaluation_interval_s: std::env::var("EVALUATION_INTERVAL_S")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(60),
            listen_addr: std::env::var("LISTEN_ADDR")
                .unwrap_or_else(|_| "0.0.0.0:8091".into()),
        }
    }

    /// Full URL for the anomaly signal snapshots endpoint.
    pub fn snapshots_url(&self) -> String {
        format!(
            "{}/internal/anomaly-signal-snapshots-v1",
            self.backend_url.trim_end_matches('/')
        )
    }
}
