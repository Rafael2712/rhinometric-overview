use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;

/// Database connection wrapper.
#[derive(Clone)]
pub struct Database {
    pub pool: PgPool,
}

impl Database {
    /// Connect to PostgreSQL with a connection pool.
    /// Max 3 connections — this engine is lightweight.
    pub async fn connect(database_url: &str) -> Result<Self, sqlx::Error> {
        let pool = PgPoolOptions::new()
            .max_connections(3)
            .acquire_timeout(std::time::Duration::from_secs(5))
            .connect(database_url)
            .await?;

        tracing::info!("Connected to PostgreSQL (pool_size=3)");
        Ok(Database { pool })
    }

    /// Health check — runs a simple query.
    pub async fn is_healthy(&self) -> bool {
        sqlx::query_scalar::<_, i32>("SELECT 1")
            .fetch_one(&self.pool)
            .await
            .is_ok()
    }
}
