import os
"""
FastAPI Application
REST API for anomaly detection service
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional, List
from datetime import datetime
import logging

from app.config import config_manager
from app.detector import AnomalyDetector

logger = logging.getLogger(__name__)

# Prometheus metrics for this service
prom_requests = Counter(
    "rhinometric_anomaly_api_requests_total",
    "Total API requests",
    ["endpoint", "method", "status"]
)
prom_anomalies_detected = Counter(
    "rhinometric_anomaly_detections_total",
    "Total anomalies detected",
    ["metric", "severity"]
)
prom_detection_duration = Histogram(
    "rhinometric_anomaly_detection_duration_seconds",
    "Time spent detecting anomalies",
    ["metric"]
)
prom_active_anomalies = Gauge(
    "rhinometric_ai_anomalies_active",
    "Current number of active anomalies"
)
prom_resolved_anomalies = Counter(
    "rhinometric_anomaly_resolved_total",
    "Total anomalies resolved",
    ["metric", "severity"]
)
prom_models_trained = Gauge(
    "rhinometric_anomaly_models_trained",
    "Number of trained models",
    ["model"]
)
prom_baselines_learned = Gauge(
    "rhinometric_baseline_count",
    "Number of learned baselines",
    ["metric_name", "hour_of_day", "day_of_week"]
)

# ============================================
# ANOMALY EXPORT METRICS (CORE FIX)
# ============================================
prom_anomaly_detected = Gauge(
    "rhinometric_anomaly_active",
    "Whether an anomaly is currently active for this metric (1=anomaly, 0=normal)",
    ["metric_name", "severity"]
)
prom_anomaly_score = Gauge(
    "rhinometric_anomaly_score",
    "Current anomaly score for metric (0-1, higher = more anomalous)",
    ["metric_name"]
)
prom_anomaly_deviation_percent = Gauge(
    "rhinometric_anomaly_deviation_percent",
    "Deviation percentage from expected baseline",
    ["metric_name"]
)
prom_anomaly_current_value = Gauge(
    "rhinometric_anomaly_current_value",
    "Current value of the metric being monitored",
    ["metric_name"]
)
prom_anomaly_expected_value = Gauge(
    "rhinometric_anomaly_expected_value",
    "Expected baseline value for the metric",
    ["metric_name"]
)

def update_anomaly_export_metrics():
    """
    Export active anomalies as Prometheus metrics
    This is the core fix for Grafana visibility
    """
    try:
        if detector is None:
            return
        
        # Get active anomalies grouped by metric
        active_by_metric = {}
        for anomaly in detector.anomalies:
            if anomaly.status == "active":
                active_by_metric[anomaly.metric_name] = anomaly
        
        # Get all configured metrics
        all_metrics = config_manager.get_enabled_metrics()
        
        # Update metrics for each configured metric
        for metric_config in all_metrics:
            metric_name = metric_config.name
            
            if metric_name in active_by_metric:
                # Anomaly active - export its data
                anomaly = active_by_metric[metric_name]
                
                # Set anomaly detected flag
                prom_anomaly_detected.labels(
                    metric_name=metric_name,
                    severity=anomaly.severity
                ).set(1)
                
                # Export anomaly details
                prom_anomaly_score.labels(metric_name=metric_name).set(anomaly.anomaly_score)
                prom_anomaly_current_value.labels(metric_name=metric_name).set(anomaly.current_value)
                prom_anomaly_expected_value.labels(metric_name=metric_name).set(anomaly.expected_value)
                
                # Export deviation percent if available
                if anomaly.deviation_percent is not None:
                    prom_anomaly_deviation_percent.labels(metric_name=metric_name).set(
                        anomaly.deviation_percent
                    )
            else:
                # No active anomaly - set to normal (0)
                prom_anomaly_detected.labels(
                    metric_name=metric_name,
                    severity="normal"
                ).set(0)
                
                # Clear other metrics (set to 0)
                prom_anomaly_score.labels(metric_name=metric_name).set(0)
                prom_anomaly_deviation_percent.labels(metric_name=metric_name).set(0)
        
        logger.debug(f"Updated anomaly export metrics: {len(active_by_metric)} active anomalies")
    except Exception as e:
        logger.error(f"Error updating anomaly export metrics: {e}")

def update_baseline_metrics():
    """Update Prometheus metrics for baselines"""
    try:
        from app.baseline_manager import baseline_manager
        from app.database import db
        
        # Clear existing metrics
        prom_baselines_learned.clear()
        
        # Get all baselines and update metrics
        baselines = db.get_all_baselines()
        for baseline in baselines:
            prom_baselines_learned.labels(
                metric_name=baseline['metric_name'],
                hour_of_day=str(baseline['hour_of_day']),
                day_of_week=str(baseline['day_of_week'])
            ).set(baseline['sample_count'])
        
        logger.debug(f"Updated baseline metrics: {len(baselines)} baselines")
    except Exception as e:
        logger.error(f"Error updating baseline metrics: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="RhinoMetric AI Anomaly Detection",
    description="Enterprise-grade ML-based anomaly detection for observability metrics",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
if config_manager.config.server.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config_manager.config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Global detector instance
detector: Optional[AnomalyDetector] = None


@app.on_event("startup")
async def startup_event():
    """Initialize detector on startup"""
    global detector
    logger.info("=" * 70)
    logger.info("RHINOMETRIC AI ANOMALY DETECTION v2.2.0")
    logger.info("=" * 70)
    
    try:
        detector = AnomalyDetector()
        await detector.initialize()
        logger.info("✓ Detector initialized successfully")
        
        # Start background detection service
        from app.main import detection_service, DetectionService
        import app.main as main_module
        main_module.detection_service = DetectionService(detector)
        await main_module.detection_service.start()
        
        # Update baseline metrics on startup
        update_baseline_metrics()
        logger.info("✓ Baseline metrics initialized")
        
        # INITIALIZE ANOMALY EXPORT METRICS ON STARTUP (CORE FIX)
        print("DEBUG: About to initialize anomaly export metrics...")
        try:
            # Initialize all metric gauges to 0
            all_metrics = config_manager.get_enabled_metrics()
            print(f"DEBUG: Got {len(all_metrics)} metrics to initialize")
            for metric_config in all_metrics:
                metric_name = metric_config.name
                prom_anomaly_detected.labels(metric_name=metric_name, severity="normal").set(0)
                prom_anomaly_score.labels(metric_name=metric_name).set(0)
                prom_anomaly_deviation_percent.labels(metric_name=metric_name).set(0)
                prom_anomaly_current_value.labels(metric_name=metric_name).set(0)
                prom_anomaly_expected_value.labels(metric_name=metric_name).set(0)
                print(f"DEBUG: Initialized gauges for {metric_name}")
            logger.info(f"✓ Anomaly export metrics initialized ({len(all_metrics)} metrics)")
            print("DEBUG: Anomaly export metrics initialization complete")
        except Exception as e:
            logger.error(f"Error initializing anomaly export metrics: {e}")
            print(f"DEBUG ERROR: {e}")
            import traceback
            traceback.print_exc()
        

        # Load persisted notification setting (defense in depth)
        try:
            persisted_enabled = _load_notification_setting()
            config_manager.config.features.enable_notifications = persisted_enabled
            logger.info(f"AI notifications loaded from persistence: enabled={persisted_enabled}")
        except Exception as notify_err:
            logger.warning(f"Failed to load notification settings: {notify_err}")

    except Exception as e:
        logger.error(f"Failed to initialize detector: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global detector
    if detector:
        logger.info("Shutting down detector...")
        await detector.cleanup()
        logger.info("✓ Cleanup complete")


# === Health and Status Endpoints ===

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    prom_requests.labels(endpoint="/health", method="GET", status="200").inc()
    
    return {
        "status": "healthy",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint"""
    if detector is None:
        prom_requests.labels(endpoint="/ready", method="GET", status="503").inc()
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/ready", method="GET", status="200").inc()
    
    return {
        "status": "ready",
        "models_trained": sum(
            1 for model in detector.ensemble.models.values() if model.trained
        ),
        "total_models": len(detector.ensemble.models)
    }


@app.get("/status", tags=["Health"])
async def get_status():
    """Get detector status and statistics"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/status", method="GET", status="200").inc()
    
    stats = detector.get_stats()
    
    # Get baseline configuration
    import os
    baseline_config = {
        "db_path": os.getenv("DB_PATH", "/app/data/ai_anomaly.db"),
        "refresh_interval": os.getenv("BASELINE_REFRESH_INTERVAL", "1h"),
        "ema_alpha": float(os.getenv("BASELINE_EMA_ALPHA", "0.1")),
        "min_samples": int(os.getenv("BASELINE_MIN_SAMPLES", "20"))
    }
    
    return {
        "status": "running",
        "version": "2.6.0",
        "statistics": stats,
        "configuration": {
            "check_interval": config_manager.config.detection.check_interval,
            "lookback_hours": config_manager.config.detection.lookback_hours,
            "metrics_enabled": len(config_manager.get_enabled_metrics()),
            "alertmanager_enabled": config_manager.config.alertmanager.enabled,
            "baseline": baseline_config
        }
    }


# === Anomaly Endpoints ===

@app.get("/anomalies", tags=["Anomalies"])
async def get_anomalies(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of anomalies to return"),
    metric: Optional[str] = Query(None, description="Filter by metric name")
):
    """Get recent anomalies"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/anomalies", method="GET", status="200").inc()
    
    anomalies = detector.get_recent_anomalies(limit=limit, metric_name=metric)
    
    # Update active anomalies gauge (only count active status)
    active_count = len([a for a in detector.anomalies if a.status == "active"])
    prom_active_anomalies.set(active_count)
    
    # UPDATE EXPORT METRICS (CORE FIX)
    update_anomaly_export_metrics()
    
    return {
        "anomalies": anomalies,
        "count": len(anomalies),
        "total_stored": len(detector.anomalies),
        "active_count": active_count,
        "filtered_by_metric": metric is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/anomalies/summary", tags=["Anomalies"])
async def get_anomaly_summary():
    """Get summary of anomalies by metric"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/anomalies/summary", method="GET", status="200").inc()
    
    # Group anomalies by metric
    summary = {}
    for anomaly in detector.anomalies:
        metric_name = anomaly.metric_name
        if metric_name not in summary:
            summary[metric_name] = {
                "total": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "latest": None
            }
        
        summary[metric_name]["total"] += 1
        summary[metric_name]["by_severity"][anomaly.severity] += 1
        summary[metric_name]["latest"] = anomaly.timestamp.isoformat()
    
    return {
        "summary": summary,
        "total_metrics_with_anomalies": len(summary),
        "timestamp": datetime.now().isoformat()
    }


# === Detection Endpoints ===

@app.post("/detect", tags=["Detection"])
async def trigger_detection(background_tasks: BackgroundTasks):
    """Manually trigger anomaly detection"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/detect", method="POST", status="202").inc()
    
    # Run detection in background
    background_tasks.add_task(detector.check_all_metrics)
    
    return {
        "status": "detection_triggered",
        "message": "Anomaly detection started in background",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/detect/{metric_name}", tags=["Detection"])
async def detect_metric(metric_name: str):
    """Detect anomalies for specific metric"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    metric_config = config_manager.get_metric(metric_name)
    if not metric_config:
        prom_requests.labels(endpoint="/detect/{metric}", method="POST", status="404").inc()
        raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")
    
    if not metric_config.enabled:
        prom_requests.labels(endpoint="/detect/{metric}", method="POST", status="400").inc()
        raise HTTPException(status_code=400, detail=f"Metric '{metric_name}' is disabled")
    
    # Detect
    start_time = datetime.now()
    result = await detector.detect_metric_anomalies(metric_config)
    duration = (datetime.now() - start_time).total_seconds()
    
    # Record metrics
    prom_detection_duration.labels(metric=metric_name).observe(duration)
    
    if result:
        prom_anomalies_detected.labels(
            metric=metric_name,
            severity=result.severity
        ).inc()
    
    prom_requests.labels(endpoint="/detect/{metric}", method="POST", status="200").inc()
    
    return {
        "metric": metric_name,
        "anomaly_detected": result is not None,
        "result": result.to_dict() if result else None,
        "detection_duration_seconds": duration,
        "timestamp": datetime.now().isoformat()
    }


# === Configuration Endpoints ===

@app.get("/metrics/config", tags=["Configuration"])
async def get_metrics_config(
    enabled_only: bool = Query(True, description="Return only enabled metrics")
):
    """Get metrics configuration"""
    prom_requests.labels(endpoint="/metrics/config", method="GET", status="200").inc()
    
    if enabled_only:
        metrics = config_manager.get_enabled_metrics()
    else:
        metrics = config_manager.config.metrics
    
    return {
        "metrics": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "enabled": m.enabled,
                "priority": m.priority,
                "models": m.models,
                "sensitivity": m.sensitivity
            }
            for m in metrics
        ],
        "count": len(metrics)
    }


@app.get("/metrics/config/{metric_name}", tags=["Configuration"])
async def get_metric_config(metric_name: str):
    """Get configuration for specific metric"""
    metric_config = config_manager.get_metric(metric_name)
    if not metric_config:
        prom_requests.labels(endpoint="/metrics/config/{metric}", method="GET", status="404").inc()
        raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")
    
    prom_requests.labels(endpoint="/metrics/config/{metric}", method="GET", status="200").inc()
    
    return metric_config.dict()


@app.post("/config/reload", tags=["Configuration"])
async def reload_config():
    """Reload configuration from file"""
    prom_requests.labels(endpoint="/config/reload", method="POST", status="200").inc()
    
    try:
        config_manager.reload()
        return {
            "status": "success",
            "message": "Configuration reloaded",
            "metrics_enabled": len(config_manager.get_enabled_metrics()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {e}")


# === Model Endpoints ===

@app.get("/models", tags=["Models"])
async def get_models():
    """Get information about ML models"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/models", method="GET", status="200").inc()
    
    models_info = []
    for name, model in detector.ensemble.models.items():
        info = {
            "name": name,
            "trained": model.trained,
            "last_trained": model.last_trained.isoformat() if model.last_trained else None,
            "config": model.config
        }
        models_info.append(info)
        
        # Update Prometheus gauge
        prom_models_trained.labels(model=name).set(1 if model.trained else 0)
    
    return {
        "models": models_info,
        "total": len(models_info),
        "trained": sum(1 for m in models_info if m["trained"])
    }


@app.post("/models/save", tags=["Models"])
async def save_models(background_tasks: BackgroundTasks):
    """Save trained models to disk"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    prom_requests.labels(endpoint="/models/save", method="POST", status="202").inc()
    
    background_tasks.add_task(detector.save_models)
    
    return {
        "status": "saving",
        "message": "Model save initiated in background",
        "timestamp": datetime.now().isoformat()
    }


# === Metrics Export Endpoint ===

@app.get("/metrics", tags=["Monitoring"], response_class=PlainTextResponse)
async def export_metrics():
    """Export Prometheus metrics"""
    if config_manager.config.metrics_export.enabled:
        # Update anomaly export metrics before generating output
        try:
            if detector is not None:
                # Get active anomalies grouped by metric
                active_by_metric = {}
                for anomaly in detector.anomalies:
                    if anomaly.status == "active":
                        active_by_metric[anomaly.metric_name] = anomaly
                
                # Get all configured metrics
                all_metrics = config_manager.get_enabled_metrics()
                
                # Update metrics for each configured metric
                for metric_config in all_metrics:
                    metric_name = metric_config.name
                    
                    if metric_name in active_by_metric:
                        # Anomaly active - export its data
                        anomaly = active_by_metric[metric_name]
                        
                        # Set anomaly detected flag
                        prom_anomaly_detected.labels(
                            metric_name=metric_name,
                            severity=anomaly.severity
                        ).set(1)
                        
                        # Export anomaly details
                        prom_anomaly_score.labels(metric_name=metric_name).set(anomaly.anomaly_score)
                        prom_anomaly_current_value.labels(metric_name=metric_name).set(anomaly.current_value)
                        prom_anomaly_expected_value.labels(metric_name=metric_name).set(anomaly.expected_value)
                        
                        # Export deviation percent if available
                        if anomaly.deviation_percent is not None:
                            prom_anomaly_deviation_percent.labels(metric_name=metric_name).set(
                                anomaly.deviation_percent
                            )
                    else:
                        # No active anomaly - set to normal (0)
                        prom_anomaly_detected.labels(
                            metric_name=metric_name,
                            severity="normal"
                        ).set(0)
                        
                        # Clear other metrics (set to 0)
                        prom_anomaly_score.labels(metric_name=metric_name).set(0)
                        prom_anomaly_deviation_percent.labels(metric_name=metric_name).set(0)
        except Exception as e:
            logger.error(f"Error updating anomaly export metrics: {e}")
        
        return PlainTextResponse(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    else:
        raise HTTPException(status_code=404, detail="Metrics export disabled")


# === Error Handlers ===

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    prom_requests.labels(endpoint="unknown", method=request.method, status="500").inc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# === Root Endpoint ===

@app.get("/", tags=["Info"])
async def root():
    """API information"""
    return {
        "service": "RhinoMetric AI Anomaly Detection",
        "version": "2.6.0",
        "description": "Enterprise ML-based anomaly detection for observability metrics",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "anomalies": "/anomalies",
            "detect": "/detect",
            "baselines": "/api/v1/baselines",
            "metrics": "/metrics"
        },
        "timestamp": datetime.now().isoformat()
    }


# === Baseline Endpoints ===

@app.get("/api/v1/baselines/metrics", tags=["Baselines"])
async def list_baseline_metrics():
    """
    Get list of all metrics with baselines
    
    Returns:
        List of metric names with baseline data
    """
    try:
        from app.baseline_manager import baseline_manager
        
        metrics = baseline_manager.get_all_metrics()
        
        prom_requests.labels(endpoint="/api/v1/baselines/metrics", method="GET", status="200").inc()
        
        return {
            "metrics": metrics,
            "count": len(metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error listing baseline metrics: {e}")
        prom_requests.labels(endpoint="/api/v1/baselines/metrics", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/baselines", tags=["Baselines"])
async def get_baselines(
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    include_details: bool = Query(False, description="Include full baseline details")
):
    """
    Get baseline data
    
    Args:
        metric: Optional metric name to filter
        include_details: Include full statistical details
    
    Returns:
        Baseline data for requested metrics
    """
    try:
        from app.baseline_manager import baseline_manager
        
        if metric:
            # Get baselines for specific metric
            baselines = baseline_manager.get_metric_baselines(metric)
            
            if not include_details:
                # Simplified response
                baselines = [
                    {
                        "hour_of_day": b["hour_of_day"],
                        "day_of_week": b["day_of_week"],
                        "expected_range": [b["p10"], b["p90"]],
                        "mean": b["mean"],
                        "last_updated": b["last_updated"]
                    }
                    for b in baselines
                ]
        else:
            # Get stats for all baselines
            stats = baseline_manager.get_stats()
            baselines = {
                "stats": stats,
                "metrics": baseline_manager.get_all_metrics()
            }
        
        prom_requests.labels(endpoint="/api/v1/baselines", method="GET", status="200").inc()
        
        return {
            "baselines": baselines,
            "metric_filter": metric,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting baselines: {e}")
        prom_requests.labels(endpoint="/api/v1/baselines", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/baselines/expected", tags=["Baselines"])
async def get_expected_value(
    metric: str = Query(..., description="Metric name"),
    timestamp: Optional[str] = Query(None, description="ISO timestamp (defaults to now)")
):
    """
    Get expected baseline value for a metric at specific time
    
    Args:
        metric: Metric name
        timestamp: ISO timestamp (optional, defaults to current time)
    
    Returns:
        Expected baseline statistics
    """
    try:
        from app.baseline_manager import baseline_manager
        from datetime import datetime
        
        # Parse timestamp
        if timestamp:
            ts = datetime.fromisoformat(timestamp)
        else:
            ts = datetime.now()
        
        # Get baseline
        metric_labels = {"metric": metric}
        baseline = baseline_manager.get_expected_value(
            metric_name=metric,
            metric_labels=metric_labels,
            timestamp=ts
        )
        
        if not baseline:
            prom_requests.labels(endpoint="/api/v1/baselines/expected", method="GET", status="404").inc()
            raise HTTPException(
                status_code=404,
                detail=f"No baseline found for metric '{metric}' at {ts.isoformat()}"
            )
        
        prom_requests.labels(endpoint="/api/v1/baselines/expected", method="GET", status="200").inc()
        
        return {
            "metric": metric,
            "timestamp": ts.isoformat(),
            "hour_of_day": ts.hour,
            "day_of_week": ts.weekday(),
            "baseline": baseline.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting expected baseline: {e}")
        prom_requests.labels(endpoint="/api/v1/baselines/expected", method="GET", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/baselines/refresh", tags=["Baselines"])
async def refresh_baselines(background_tasks: BackgroundTasks):
    """
    Trigger manual baseline refresh for all metrics
    
    This will recalculate baselines in the background.
    
    Returns:
        Confirmation message
    """
    try:
        from app.baseline_manager import baseline_manager
        from app.prom_client import PrometheusClient
        import numpy as np
        
        async def refresh_all():
            """Background task to refresh all baselines"""
            try:
                logger.info("Manual baseline refresh triggered")
                enabled_metrics = config_manager.get_enabled_metrics()
                prometheus = PrometheusClient(config_manager.config.prometheus)
                
                updated_count = 0
                for metric_config in enabled_metrics:
                    try:
                        values = await prometheus.fetch_metric_values(
                            metric_config.query,
                            hours=config_manager.config.detection.lookback_hours
                        )
                        
                        if len(values) >= baseline_manager.min_samples:
                            metric_labels = {"metric": metric_config.name}
                            baseline_manager.update_baseline(
                                metric_name=metric_config.name,
                                metric_labels=metric_labels,
                                values=np.array(values)
                            )
                            updated_count += 1
                    except Exception as e:
                        logger.error(f"Error refreshing baseline for {metric_config.name}: {e}")
                
                await prometheus.close()
                logger.info(f"Manual baseline refresh completed: {updated_count} baselines updated")
            
            except Exception as e:
                logger.error(f"Error in baseline refresh task: {e}")
        
        # Add to background tasks
        background_tasks.add_task(refresh_all)
        
        prom_requests.labels(endpoint="/api/v1/baselines/refresh", method="POST", status="202").inc()
        
        return {
            "status": "accepted",
            "message": "Baseline refresh started in background",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error triggering baseline refresh: {e}")
        prom_requests.labels(endpoint="/api/v1/baselines/refresh", method="POST", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SETTINGS: Runtime notification toggle (synced from console-backend)
# =============================================================================

NOTIFICATION_SETTINGS_FILE = "/app/data/notification_settings.json"

def _load_notification_setting() -> bool:
    """Load persisted notification setting from disk."""
    import json
    try:
        if os.path.exists(NOTIFICATION_SETTINGS_FILE):
            with open(NOTIFICATION_SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return data.get("enabled", False)
    except Exception as e:
        logger.warning(f"Failed to load notification settings: {e}")
    return False

def _save_notification_setting(enabled: bool):
    """Persist notification setting to disk."""
    import json
    try:
        os.makedirs(os.path.dirname(NOTIFICATION_SETTINGS_FILE), exist_ok=True)
        with open(NOTIFICATION_SETTINGS_FILE, "w") as f:
            json.dump({"enabled": enabled}, f)
        logger.info(f"Notification setting persisted: enabled={enabled}")
    except Exception as e:
        logger.error(f"Failed to save notification settings: {e}")


@app.post("/api/settings/notifications", tags=["Settings"])
async def update_notification_settings(body: dict):
    """
    Toggle AI anomaly notifications at runtime.
    Called by console-backend when the UI toggle changes.
    
    Body: {"enabled": true|false}
    
    Effects:
    - Updates config.features.enable_notifications in memory
    - Persists to /app/data/notification_settings.json
    """
    enabled = body.get("enabled")
    if enabled is None:
        raise HTTPException(status_code=400, detail="'enabled' field required")
    
    enabled = bool(enabled)
    
    # Update in-memory config
    config_manager.config.features.enable_notifications = enabled
    
    # Persist to disk
    _save_notification_setting(enabled)
    
    state = "enabled" if enabled else "disabled"
    logger.info(f"AI notifications {state} via runtime API")
    
    prom_requests.labels(
        endpoint="/api/settings/notifications", method="POST", status="200"
    ).inc()
    
    return {
        "status": "ok",
        "notifications_enabled": enabled,
        "message": f"AI anomaly notifications {state}",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/settings/notifications", tags=["Settings"])
async def get_notification_settings():
    """Get current notification setting."""
    enabled = config_manager.config.features.enable_notifications
    return {
        "notifications_enabled": enabled,
        "persisted": os.path.exists(NOTIFICATION_SETTINGS_FILE)
    }
