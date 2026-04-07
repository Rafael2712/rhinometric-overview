use std::time::Instant;

use chrono::Utc;
use prometheus::{register_counter, register_gauge, register_histogram, Counter, Gauge, Histogram};
use tokio::time::{sleep, Duration};

use crate::client::backend::BackendClient;
use crate::persistence::db::Database;
use crate::persistence::{history, repository};
use crate::scoring::engine;
use crate::threshold::SharedThresholdConfig;

/// Prometheus metrics for the worker.
struct WorkerMetrics {
    cycles_total: Counter,
    cycle_errors_total: Counter,
    cycle_duration_seconds: Histogram,
    services_evaluated: Gauge,
    anomalies_active: Gauge,
    max_score: Gauge,
}

impl WorkerMetrics {
    fn new() -> Self {
        Self {
            cycles_total: register_counter!(
                "anomaly_engine_cycles_total",
                "Total scoring cycles executed"
            )
            .unwrap(),
            cycle_errors_total: register_counter!(
                "anomaly_engine_cycle_errors_total",
                "Total scoring cycle errors"
            )
            .unwrap(),
            cycle_duration_seconds: register_histogram!(
                "anomaly_engine_cycle_duration_seconds",
                "Duration of each scoring cycle"
            )
            .unwrap(),
            services_evaluated: register_gauge!(
                "anomaly_engine_services_evaluated",
                "Number of services evaluated in last cycle"
            )
            .unwrap(),
            anomalies_active: register_gauge!(
                "anomaly_engine_anomalies_active",
                "Number of currently active anomalies"
            )
            .unwrap(),
            max_score: register_gauge!(
                "anomaly_engine_max_score",
                "Maximum anomaly score in last cycle"
            )
            .unwrap(),
        }
    }
}

/// Start the worker loop. Runs indefinitely on the given interval.
pub async fn run(db: Database, client: BackendClient, interval_secs: u64, threshold: SharedThresholdConfig) {
    let metrics = WorkerMetrics::new();

    tracing::info!("Worker started (interval={}s)", interval_secs);

    loop {
        let cycle_start = Instant::now();

        // Hot-reload threshold config from disk each cycle
        crate::threshold::reload(&threshold, "config/anomaly_v1.yaml").await;

        match run_cycle(&db, &client, &metrics, &threshold).await {
            Ok(()) => {
                metrics.cycles_total.inc();
            }
            Err(e) => {
                metrics.cycle_errors_total.inc();
                tracing::error!("Scoring cycle failed: {e}");
            }
        }

        let elapsed = cycle_start.elapsed();
        metrics
            .cycle_duration_seconds
            .observe(elapsed.as_secs_f64());

        tracing::debug!("Cycle completed in {:.1}ms", elapsed.as_secs_f64() * 1000.0);

        sleep(Duration::from_secs(interval_secs)).await;
    }
}

/// Execute a single scoring cycle.
async fn run_cycle(
    db: &Database,
    client: &BackendClient,
    metrics: &WorkerMetrics,
    threshold: &SharedThresholdConfig,
) -> Result<(), Box<dyn std::error::Error>> {
    let cycle_start = Instant::now();

    // 1. Fetch snapshots from backend
    let snapshot_resp = client.fetch_snapshots().await?;

    let snapshots = &snapshot_resp.snapshots;
    let num_services = snapshots.len();
    metrics.services_evaluated.set(num_services as f64);

    if snapshots.is_empty() {
        tracing::warn!("No snapshots received — skipping cycle");
        return Ok(());
    }

    // 2. Score each service
    let mut active_service_ids = Vec::new();
    let mut active_fingerprints = Vec::new();
    let mut anomaly_count = 0u32;
    let mut max_score = 0.0_f64;

    let cfg = threshold.read().await;
    let active_threshold = cfg.scoring.active_threshold;
    let anomalous_threshold = cfg.scoring.anomalous_threshold;
    let cat_trigger = cfg.scoring.category_trigger_threshold;
    let pred_cfg = cfg.prediction.clone();
    drop(cfg);

    for snap in snapshots {
        let eval_start = Instant::now();
        let mut output = engine::evaluate(snap, &pred_cfg);
        output.evaluation_duration_ms = eval_start.elapsed().as_millis() as i32;

        // Apply hot-reloaded thresholds
        output.is_anomalous = output.score > anomalous_threshold;
        let cat = &output.category_scores;
        output.triggered_categories_count = [cat.latency, cat.availability, cat.error, cat.ssl]
            .iter()
            .filter(|&&s| s > cat_trigger)
            .count() as i16;

        if output.score > max_score {
            max_score = output.score;
        }

        if output.score > 15.0 {
            anomaly_count += 1;
            active_service_ids.push(output.service_id);
            active_fingerprints.push(output.fingerprint.clone());
        }

        // 3. Persist result (upsert)
        repository::upsert_result(&db.pool, &output).await?;
    }

    // 4. Resolve stale anomalies
    let resolved = repository::resolve_stale(
        &db.pool,
        &active_service_ids,
        &active_fingerprints,
        Utc::now(),
    )
    .await?;

    if resolved > 0 {
        tracing::info!("Resolved {resolved} stale anomalies");
    }

    // 5. Record history
    let cycle_ms = cycle_start.elapsed().as_millis() as i64;
    let warnings_str = if !snapshot_resp.warnings.is_empty() {
        Some(snapshot_resp.warnings.join("; "))
    } else {
        None
    };

    history::record_cycle(
        &db.pool,
        num_services as i32,
        anomaly_count as i32,
        max_score,
        cycle_ms,
        warnings_str,
    )
    .await?;

    // 6. Update Prometheus gauges
    metrics.anomalies_active.set(anomaly_count as f64);
    metrics.max_score.set(max_score);

    tracing::info!(
        "Cycle complete: {num_services} services, {anomaly_count} anomalies, max_score={max_score:.1}, {cycle_ms}ms"
    );

    Ok(())
}
