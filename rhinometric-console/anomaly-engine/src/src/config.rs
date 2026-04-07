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
    /// Python anomaly service URL (for comparison endpoint)
    pub python_anomaly_url: String,
    /// OpenAI API key for LLM explanation layer
    pub openai_api_key: String,
    /// OpenAI model name (default: gpt-4o-mini)
    pub openai_model: String,
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
            python_anomaly_url: std::env::var("PYTHON_ANOMALY_URL")
                .unwrap_or_else(|_| "http://rhinometric-ai-anomaly:8085".into()),
            openai_api_key: std::env::var("OPENAI_API_KEY")
                .unwrap_or_default(),
            openai_model: std::env::var("OPENAI_MODEL")
                .unwrap_or_else(|_| "gpt-4o-mini".into()),
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
