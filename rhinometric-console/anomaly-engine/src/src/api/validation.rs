use axum::{extract::State, Json};
use serde::{Deserialize, Serialize};

use crate::server::AppState;

// ─── GET /api/v2/anomalies/validation-summary ───

#[derive(Serialize)]
pub struct ValidationSummaryResponse {
    pub total_evaluated: i64,
    pub total_active: i64,
    pub total_anomalous: i64,
    pub avg_score: f64,
    pub max_score: i64,
    pub avg_confidence: f64,
    pub avg_baseline_deviation_pct: f64,
    pub avg_triggered_categories: f64,
    pub avg_evaluation_duration_ms: f64,
    pub avg_latency_trend_slope: f64,
    pub avg_log_error_burst_ratio: f64,
    pub pct_positive_trend: f64,
    pub pct_burst_detected: f64,
    pub avg_trace_bottleneck_score: f64,
    pub avg_trace_error_rate: f64,
    pub avg_trace_p95_latency: f64,
    pub total_slow_operations: i64,
    pub avg_predicted_risk_score: f64,
    pub predicted_high_count: i64,
    pub predicted_critical_count: i64,
    pub predicted_with_horizon_count: i64,
    pub severity_distribution: Vec<SeverityBucket>,
    pub score_histogram: Vec<ScoreBucket>,
}

#[derive(Serialize)]
pub struct SeverityBucket {
    pub severity: String,
    pub count: i64,
}

#[derive(Serialize)]
pub struct ScoreBucket {
    pub range: String,
    pub count: i64,
}

pub async fn validation_summary(
    State(state): State<AppState>,
) -> Result<Json<ValidationSummaryResponse>, axum::http::StatusCode> {
    // Aggregate stats
    let stats = sqlx::query_as::<_, AggRow>(
        r#"
        SELECT
            count(*) AS total_evaluated,
            count(*) FILTER (WHERE status = 'active') AS total_active,
            count(*) FILTER (WHERE is_anomalous = true) AS total_anomalous,
            COALESCE(avg(anomaly_score), 0)::float8 AS avg_score,
            COALESCE(max(anomaly_score), 0)::bigint AS max_score,
            COALESCE(avg(confidence), 0)::float8 AS avg_confidence,
            COALESCE(avg(baseline_deviation_pct), 0)::float8 AS avg_baseline_deviation_pct,
            COALESCE(avg(triggered_categories_count), 0)::float8 AS avg_triggered_categories,
            COALESCE(avg(evaluation_duration_ms), 0)::float8 AS avg_evaluation_duration_ms,
            COALESCE(avg(latency_trend_slope), 0)::float8 AS avg_latency_trend_slope,
            COALESCE(avg(log_error_burst_ratio), 0)::float8 AS avg_log_error_burst_ratio,
            COALESCE(100.0 * count(*) FILTER (WHERE latency_trend_slope > 0.15) / NULLIF(count(*), 0), 0)::float8 AS pct_positive_trend,
            COALESCE(100.0 * count(*) FILTER (WHERE log_error_burst_ratio > 3.0) / NULLIF(count(*), 0), 0)::float8 AS pct_burst_detected,
            COALESCE(avg(trace_bottleneck_score), 0)::float8 AS avg_trace_bottleneck_score,
            COALESCE(avg(trace_error_rate), 0)::float8 AS avg_trace_error_rate,
            COALESCE(avg(trace_p95_latency_ms), 0)::float8 AS avg_trace_p95_latency,
            COALESCE(sum(trace_slow_operations), 0)::bigint AS total_slow_operations,
            COALESCE(avg(predicted_risk_score), 0)::float8 AS avg_predicted_risk_score,
            count(*) FILTER (WHERE predicted_risk_level = 'high')::bigint AS predicted_high_count,
            count(*) FILTER (WHERE predicted_risk_level = 'critical')::bigint AS predicted_critical_count,
            count(*) FILTER (WHERE predicted_horizon_minutes IS NOT NULL)::bigint AS predicted_with_horizon_count
        FROM anomaly_engine_results_v1
        "#,
    )
    .fetch_one(&state.db.pool)
    .await
    .map_err(|e| {
        tracing::error!("DB error in validation_summary: {e}");
        axum::http::StatusCode::INTERNAL_SERVER_ERROR
    })?;

    // Severity distribution
    let severity_rows = sqlx::query_as::<_, SeverityRow>(
        r#"
        SELECT severity, count(*) AS count
        FROM anomaly_engine_results_v1
        WHERE status = 'active'
        GROUP BY severity ORDER BY count DESC
        "#,
    )
    .fetch_all(&state.db.pool)
    .await
    .map_err(|e| {
        tracing::error!("DB error: {e}");
        axum::http::StatusCode::INTERNAL_SERVER_ERROR
    })?;

    let severity_distribution = severity_rows
        .into_iter()
        .map(|r| SeverityBucket {
            severity: r.severity,
            count: r.count,
        })
        .collect();

    // Score histogram (buckets: 0-15, 16-35, 36-60, 61-80, 81-100)
    let score_rows = sqlx::query_as::<_, ScoreRow>(
        r#"
        SELECT
            CASE
                WHEN anomaly_score <= 15 THEN '0-15'
                WHEN anomaly_score <= 35 THEN '16-35'
                WHEN anomaly_score <= 60 THEN '36-60'
                WHEN anomaly_score <= 80 THEN '61-80'
                ELSE '81-100'
            END AS range,
            count(*) AS count
        FROM anomaly_engine_results_v1
        GROUP BY range ORDER BY range
        "#,
    )
    .fetch_all(&state.db.pool)
    .await
    .map_err(|e| {
        tracing::error!("DB error: {e}");
        axum::http::StatusCode::INTERNAL_SERVER_ERROR
    })?;

    let score_histogram = score_rows
        .into_iter()
        .map(|r| ScoreBucket {
            range: r.range,
            count: r.count,
        })
        .collect();

    Ok(Json(ValidationSummaryResponse {
        total_evaluated: stats.total_evaluated,
        total_active: stats.total_active,
        total_anomalous: stats.total_anomalous,
        avg_score: stats.avg_score,
        max_score: stats.max_score,
        avg_confidence: stats.avg_confidence,
        avg_baseline_deviation_pct: stats.avg_baseline_deviation_pct,
        avg_triggered_categories: stats.avg_triggered_categories,
        avg_evaluation_duration_ms: stats.avg_evaluation_duration_ms,
        avg_latency_trend_slope: stats.avg_latency_trend_slope,
        avg_log_error_burst_ratio: stats.avg_log_error_burst_ratio,
        pct_positive_trend: stats.pct_positive_trend,
        pct_burst_detected: stats.pct_burst_detected,
        avg_trace_bottleneck_score: stats.avg_trace_bottleneck_score,
        avg_trace_error_rate: stats.avg_trace_error_rate,
        avg_trace_p95_latency: stats.avg_trace_p95_latency,
        total_slow_operations: stats.total_slow_operations,
        avg_predicted_risk_score: stats.avg_predicted_risk_score,
        predicted_high_count: stats.predicted_high_count,
        predicted_critical_count: stats.predicted_critical_count,
        predicted_with_horizon_count: stats.predicted_with_horizon_count,
        severity_distribution,
        score_histogram,
    }))
}

#[derive(sqlx::FromRow)]
struct AggRow {
    total_evaluated: i64,
    total_active: i64,
    total_anomalous: i64,
    avg_score: f64,
    max_score: i64,
    avg_confidence: f64,
    avg_baseline_deviation_pct: f64,
    avg_triggered_categories: f64,
    avg_evaluation_duration_ms: f64,
    avg_latency_trend_slope: f64,
    avg_log_error_burst_ratio: f64,
    pct_positive_trend: f64,
    pct_burst_detected: f64,
    avg_trace_bottleneck_score: f64,
    avg_trace_error_rate: f64,
    avg_trace_p95_latency: f64,
    total_slow_operations: i64,
    avg_predicted_risk_score: f64,
    predicted_high_count: i64,
    predicted_critical_count: i64,
    predicted_with_horizon_count: i64,
}

#[derive(sqlx::FromRow)]
struct SeverityRow {
    severity: String,
    count: i64,
}

#[derive(sqlx::FromRow)]
struct ScoreRow {
    range: String,
    count: i64,
}

// ─── GET /api/v2/anomalies/compare-python ───

#[derive(Serialize)]
pub struct CompareResponse {
    pub rust_v2_count: usize,
    pub python_v1_count: usize,
    pub matched_services: Vec<ServiceComparison>,
    pub rust_only: Vec<String>,
    pub python_only: Vec<String>,
}

#[derive(Serialize)]
pub struct ServiceComparison {
    pub service_name: String,
    pub rust_score: i16,
    pub rust_severity: String,
    pub rust_confidence: f32,
    pub python_anomaly_score: f64,
    pub python_severity: String,
    pub python_confidence: f64,
    pub python_deviation_percent: f64,
    pub agreement: String,
}

/// Python anomaly JSON shape (flat entry from /anomalies)
#[derive(Deserialize)]
struct PythonAnomaly {
    #[serde(default)]
    entity_name: String,
    #[serde(default)]
    entity_type: String,
    #[serde(default)]
    is_anomaly: bool,
    #[serde(default)]
    anomaly_score: f64,
    #[serde(default)]
    confidence: f64,
    #[serde(default)]
    severity: String,
    #[serde(default)]
    deviation_percent: f64,
    #[serde(default)]
    status: String,
}

/// Wrapper for the Python /anomalies response
#[derive(Deserialize)]
struct PythonAnomalyResponse {
    anomalies: Vec<PythonAnomaly>,
}

pub async fn compare_python(
    State(state): State<AppState>,
) -> Result<Json<CompareResponse>, axum::http::StatusCode> {
    // 1. Get Rust V2 active anomalies
    let rust_rows = crate::persistence::repository::get_active_anomalies(&state.db.pool)
        .await
        .map_err(|e| {
            tracing::error!("DB error fetching Rust anomalies: {e}");
            axum::http::StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // 2. Fetch Python anomalies
    let python_url = format!("{}/anomalies", state.python_anomaly_url.trim_end_matches('/'));
    let python_resp: PythonAnomalyResponse = reqwest::get(&python_url)
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch Python anomalies: {e}");
            axum::http::StatusCode::BAD_GATEWAY
        })?
        .json()
        .await
        .map_err(|e| {
            tracing::error!("Failed to parse Python anomalies: {e}");
            axum::http::StatusCode::BAD_GATEWAY
        })?;

    let python_anomalies = python_resp.anomalies;

    // 3. Build Python service-level map (aggregate per entity_name where entity_type=service)
    let mut python_map: std::collections::HashMap<String, PythonServiceAgg> =
        std::collections::HashMap::new();

    for pa in &python_anomalies {
        if pa.entity_type != "service" || pa.status != "active" {
            continue;
        }
        let entry = python_map.entry(pa.entity_name.clone()).or_insert(PythonServiceAgg {
            worst_score: 0.0,
            worst_severity: "low".into(),
            max_confidence: 0.0,
            max_deviation: 0.0,
            count: 0,
        });
        entry.count += 1;
        if pa.anomaly_score.abs() > entry.worst_score.abs() {
            entry.worst_score = pa.anomaly_score;
            entry.worst_severity = pa.severity.clone();
        }
        if pa.confidence > entry.max_confidence {
            entry.max_confidence = pa.confidence;
        }
        if pa.deviation_percent.abs() > entry.max_deviation.abs() {
            entry.max_deviation = pa.deviation_percent;
        }
    }

    // 4. Match
    let mut matched = Vec::new();
    let mut rust_only = Vec::new();

    let rust_names: std::collections::HashSet<String> =
        rust_rows.iter().map(|r| r.service_name.clone()).collect();
    let python_names: std::collections::HashSet<String> =
        python_map.keys().cloned().collect();

    for row in &rust_rows {
        if let Some(py) = python_map.get(&row.service_name) {
            let agreement = if row.anomaly_score > 15 && py.worst_score.abs() > 0.1 {
                "both_flagged"
            } else if row.anomaly_score <= 15 && py.worst_score.abs() <= 0.1 {
                "both_normal"
            } else {
                "disagree"
            };
            matched.push(ServiceComparison {
                service_name: row.service_name.clone(),
                rust_score: row.anomaly_score,
                rust_severity: row.severity.clone(),
                rust_confidence: row.confidence,
                python_anomaly_score: py.worst_score,
                python_severity: py.worst_severity.clone(),
                python_confidence: py.max_confidence,
                python_deviation_percent: py.max_deviation,
                agreement: agreement.into(),
            });
        } else {
            rust_only.push(row.service_name.clone());
        }
    }

    let python_only: Vec<String> = python_names.difference(&rust_names).cloned().collect();

    Ok(Json(CompareResponse {
        rust_v2_count: rust_rows.len(),
        python_v1_count: python_map.len(),
        matched_services: matched,
        rust_only,
        python_only,
    }))
}

struct PythonServiceAgg {
    worst_score: f64,
    worst_severity: String,
    max_confidence: f64,
    max_deviation: f64,
    count: usize,
}
