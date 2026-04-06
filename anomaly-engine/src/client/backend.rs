use crate::models::snapshot::SnapshotResponse;
use reqwest::Client;
use std::time::Duration;

/// HTTP client for fetching signal snapshots from the backend.
#[derive(Clone)]
pub struct BackendClient {
    client: Client,
    snapshots_url: String,
}

impl BackendClient {
    pub fn new(snapshots_url: String) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(10))
            .connect_timeout(Duration::from_secs(5))
            .build()
            .expect("Failed to build HTTP client");

        Self {
            client,
            snapshots_url,
        }
    }

    /// Fetch all service signal snapshots from the backend.
    pub async fn fetch_snapshots(&self) -> Result<SnapshotResponse, BackendError> {
        tracing::debug!("Fetching snapshots from {}", self.snapshots_url);

        let resp = self
            .client
            .get(&self.snapshots_url)
            .header("X-Internal-Token", "anomaly-engine-v1")
            .send()
            .await
            .map_err(|e| BackendError::Network(e.to_string()))?;

        let status = resp.status();
        if !status.is_success() {
            let body = resp.text().await.unwrap_or_default();
            return Err(BackendError::Http {
                status: status.as_u16(),
                body,
            });
        }

        let body_text = resp.text().await
            .map_err(|e| BackendError::Parse(format!("Failed to read body: {e}")))?;

        tracing::debug!("Raw response (first 500 chars): {}", &body_text[..body_text.len().min(500)]);

        let snapshot_resp: SnapshotResponse = serde_json::from_str(&body_text)
            .map_err(|e| BackendError::Parse(format!("JSON parse error at line {} col {}: {e}", e.line(), e.column())))?;

        tracing::info!(
            "Received {} snapshots (assembled in {}ms)",
            snapshot_resp.snapshots.len(),
            snapshot_resp.assembly_duration_ms
        );

        Ok(snapshot_resp)
    }
}

#[derive(Debug, thiserror::Error)]
pub enum BackendError {
    #[error("Network error: {0}")]
    Network(String),
    #[error("HTTP {status}: {body}")]
    Http { status: u16, body: String },
    #[error("Parse error: {0}")]
    Parse(String),
}
