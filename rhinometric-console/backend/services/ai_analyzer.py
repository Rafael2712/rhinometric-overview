"""
AI Analyzer for External Services - Intelligence Engine.

Provides statistical analysis, anomaly detection, trend prediction,
and smart recommendations using check history data.
No external AI service required — uses pure statistical methods.
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func as sqla_func, and_

from models.external_service import ExternalService, ServiceStatus
from models.external_service_check import ExternalServiceCheck

logger = logging.getLogger("rhinometric.ai_analyzer")

# ── Constants ─────────────────────────────────────────────────────
TREND_WINDOW_HOURS = 24
ANOMALY_Z_THRESHOLD = 2.5        # Z-score threshold for anomaly
DEGRADATION_THRESHOLD_PCT = 20   # 20% latency increase = degradation warning
PREDICTION_HOURS = 72            # Predict next 72 hours
MIN_CHECKS_FOR_ANALYSIS = 10     # Minimum checks needed


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0

def _std(values: List[float], mean_val: float) -> float:
    if len(values) < 2:
        return 0.0
    return math.sqrt(sum((v - mean_val) ** 2 for v in values) / (len(values) - 1))

def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(int(len(sorted_values) * pct), len(sorted_values) - 1)
    return sorted_values[idx]

def _linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """Returns (slope, intercept, r_squared)."""
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    x_mean = _mean(x)
    y_mean = _mean(y)
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    ss_yy = sum((yi - y_mean) ** 2 for yi in y)
    if ss_xx == 0:
        return 0.0, y_mean, 0.0
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 0.0
    return slope, intercept, r_squared


def analyze_service(db: Session, service_id: int, hours: int = 24) -> Dict:
    """Full AI analysis for a single external service."""
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        return {"error": "Service not found"}

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    checks = (
        db.query(ExternalServiceCheck)
        .filter(
            ExternalServiceCheck.service_id == service_id,
            ExternalServiceCheck.checked_at >= since,
        )
        .order_by(ExternalServiceCheck.checked_at.asc())
        .all()
    )

    total = len(checks)
    if total < MIN_CHECKS_FOR_ANALYSIS:
        return {
            "service_id": service_id,
            "service_name": svc.name,
            "status": "insufficient_data",
            "message": f"Need at least {MIN_CHECKS_FOR_ANALYSIS} checks, have {total}",
            "total_checks": total,
            "period_hours": hours,
        }

    # ── Basic Metrics ──
    latencies = [c.response_time_ms for c in checks if c.response_time_ms and c.response_time_ms > 0]
    successes = sum(1 for c in checks if c.status == "up")
    failures = sum(1 for c in checks if c.status in ("down", "error"))
    availability_pct = round((successes / total) * 100, 2) if total else 0

    # ── Latency Analysis ──
    latency_analysis = _analyze_latency(latencies)

    # ── Trend Detection ──
    trend = _detect_trend(checks)

    # ── Anomaly Detection ──
    anomalies = _detect_anomalies(checks, latencies)

    # ── Failure Patterns ──
    failure_patterns = _analyze_failure_patterns(checks)

    # ── Predictions ──
    predictions = _generate_predictions(checks, latencies, svc)

    # ── Recommendations ──
    recommendations = _generate_recommendations(
        svc, availability_pct, latency_analysis, trend,
        anomalies, failure_patterns, predictions
    )

    # ── Risk Score (0-100, lower is better) ──
    risk_score = _compute_risk_score(
        availability_pct, latency_analysis, trend,
        anomalies, failure_patterns
    )

    return {
        "service_id": service_id,
        "service_name": svc.name,
        "service_type": svc.service_type.value if svc.service_type else "unknown",
        "current_status": svc.status.value if svc.status else "unknown",
        "period_hours": hours,
        "total_checks": total,
        "availability_pct": availability_pct,
        "latency": latency_analysis,
        "trend": trend,
        "anomalies": anomalies,
        "failure_patterns": failure_patterns,
        "predictions": predictions,
        "recommendations": recommendations,
        "risk_score": risk_score,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def _analyze_latency(latencies: List[float]) -> Dict:
    if not latencies:
        return {"status": "no_data"}
    sorted_lat = sorted(latencies)
    mean_val = _mean(latencies)
    std_val = _std(latencies, mean_val)
    return {
        "mean_ms": round(mean_val, 2),
        "median_ms": round(_percentile(sorted_lat, 0.50), 2),
        "p95_ms": round(_percentile(sorted_lat, 0.95), 2),
        "p99_ms": round(_percentile(sorted_lat, 0.99), 2),
        "min_ms": round(sorted_lat[0], 2),
        "max_ms": round(sorted_lat[-1], 2),
        "std_ms": round(std_val, 2),
        "cv_pct": round((std_val / mean_val) * 100, 1) if mean_val > 0 else 0,
        "sample_count": len(latencies),
    }


def _detect_trend(checks: List) -> Dict:
    """Detect latency and availability trends using linear regression."""
    latency_points = [
        (c.checked_at.timestamp(), c.response_time_ms)
        for c in checks
        if c.response_time_ms and c.response_time_ms > 0
    ]
    if len(latency_points) < 5:
        return {"latency_direction": "insufficient_data", "availability_direction": "insufficient_data"}

    x = [p[0] for p in latency_points]
    y = [p[1] for p in latency_points]
    slope, _, r_sq = _linear_regression(x, y)

    # Normalize slope to ms per hour
    slope_per_hour = slope * 3600

    if abs(slope_per_hour) < 0.5:
        lat_direction = "stable"
    elif slope_per_hour > 0:
        lat_direction = "increasing"
    else:
        lat_direction = "decreasing"

    # Availability trend: compare first half vs second half
    mid = len(checks) // 2
    first_half = checks[:mid]
    second_half = checks[mid:]
    avail_first = sum(1 for c in first_half if c.status == "up") / len(first_half) * 100 if first_half else 100
    avail_second = sum(1 for c in second_half if c.status == "up") / len(second_half) * 100 if second_half else 100
    avail_delta = avail_second - avail_first

    if abs(avail_delta) < 1:
        avail_direction = "stable"
    elif avail_delta > 0:
        avail_direction = "improving"
    else:
        avail_direction = "degrading"

    return {
        "latency_direction": lat_direction,
        "latency_slope_ms_per_hour": round(slope_per_hour, 3),
        "latency_r_squared": round(r_sq, 3),
        "availability_direction": avail_direction,
        "availability_first_half_pct": round(avail_first, 1),
        "availability_second_half_pct": round(avail_second, 1),
        "availability_delta_pct": round(avail_delta, 1),
    }


def _detect_anomalies(checks: List, latencies: List[float]) -> Dict:
    """Z-score based anomaly detection on latency values."""
    if len(latencies) < MIN_CHECKS_FOR_ANALYSIS:
        return {"count": 0, "details": [], "status": "insufficient_data"}

    mean_val = _mean(latencies)
    std_val = _std(latencies, mean_val)
    if std_val == 0:
        return {"count": 0, "details": [], "status": "no_variance"}

    anomaly_details = []
    for c in checks:
        if c.response_time_ms and c.response_time_ms > 0:
            z = abs((c.response_time_ms - mean_val) / std_val)
            if z >= ANOMALY_Z_THRESHOLD:
                anomaly_details.append({
                    "timestamp": c.checked_at.isoformat(),
                    "value_ms": round(c.response_time_ms, 2),
                    "z_score": round(z, 2),
                    "direction": "high" if c.response_time_ms > mean_val else "low",
                    "severity": "critical" if z >= 4.0 else "warning" if z >= 3.0 else "info",
                })

    return {
        "count": len(anomaly_details),
        "threshold_z": ANOMALY_Z_THRESHOLD,
        "mean_ms": round(mean_val, 2),
        "std_ms": round(std_val, 2),
        "details": anomaly_details[-10:],  # Last 10 anomalies
    }


def _analyze_failure_patterns(checks: List) -> Dict:
    """Analyze failure distribution and patterns."""
    if not checks:
        return {"total_failures": 0}

    failures = [c for c in checks if c.status in ("down", "error")]
    if not failures:
        return {"total_failures": 0, "pattern": "none", "health": "excellent"}

    total_failures = len(failures)

    # Check for consecutive failure bursts
    bursts = []
    current_burst = 0
    for c in checks:
        if c.status in ("down", "error"):
            current_burst += 1
        else:
            if current_burst > 0:
                bursts.append(current_burst)
            current_burst = 0
    if current_burst > 0:
        bursts.append(current_burst)

    max_burst = max(bursts) if bursts else 0
    avg_burst = round(_mean([float(b) for b in bursts]), 1) if bursts else 0

    # Classify pattern
    if max_burst >= 10:
        pattern = "sustained_outage"
    elif len(bursts) > 5 and max_burst < 3:
        pattern = "intermittent_flapping"
    elif len(bursts) <= 2 and max_burst >= 3:
        pattern = "isolated_outage"
    elif total_failures <= 2:
        pattern = "rare_blips"
    else:
        pattern = "mixed"

    return {
        "total_failures": total_failures,
        "failure_rate_pct": round((total_failures / len(checks)) * 100, 1),
        "burst_count": len(bursts),
        "max_consecutive_failures": max_burst,
        "avg_burst_length": avg_burst,
        "pattern": pattern,
        "currently_failing": checks[-1].status in ("down", "error") if checks else False,
    }


def _generate_predictions(checks: List, latencies: List[float], svc) -> Dict:
    """Generate forward-looking predictions."""
    predictions = {}

    # Latency prediction using trend
    if len(latencies) >= MIN_CHECKS_FOR_ANALYSIS:
        lat_points = [
            (c.checked_at.timestamp(), c.response_time_ms)
            for c in checks
            if c.response_time_ms and c.response_time_ms > 0
        ]
        if len(lat_points) >= 5:
            x = [p[0] for p in lat_points]
            y = [p[1] for p in lat_points]
            slope, intercept, r_sq = _linear_regression(x, y)
            future_ts = datetime.now(timezone.utc).timestamp() + PREDICTION_HOURS * 3600
            predicted_latency = slope * future_ts + intercept
            if predicted_latency > 0 and r_sq > 0.1:
                predictions["latency_72h_ms"] = round(predicted_latency, 2)
                predictions["latency_trend_confidence"] = round(r_sq, 2)

    # SSL expiry prediction (for HTTP services)
    if svc.service_type and svc.service_type.value == "http":
        config = svc.config or {}
        url = config.get("url", "")
        if url.startswith("https://"):
            predictions["ssl_monitoring"] = True

    # Failure probability based on recent failure rate
    recent = checks[-20:] if len(checks) >= 20 else checks
    recent_failures = sum(1 for c in recent if c.status in ("down", "error"))
    failure_prob = round((recent_failures / len(recent)) * 100, 1) if recent else 0
    predictions["failure_probability_next_hour_pct"] = failure_prob

    # Availability forecast
    if len(checks) >= 30:
        avail = sum(1 for c in checks if c.status == "up") / len(checks) * 100
        predictions["availability_forecast_24h_pct"] = round(avail, 2)

    return predictions


def _generate_recommendations(
    svc, availability_pct, latency_analysis, trend,
    anomalies, failure_patterns, predictions
) -> List[Dict]:
    """Generate actionable recommendations based on analysis."""
    recs = []
    priority = 0

    # Availability issues
    if availability_pct < 95:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "availability",
            "severity": "critical" if availability_pct < 90 else "warning",
            "title": "Low availability detected",
            "description": f"Service availability is {availability_pct}%, below the 95% SLA threshold.",
            "action": "Investigate root cause of failures. Check server logs, network connectivity, and resource utilization.",
        })

    # High latency
    if latency_analysis.get("p95_ms", 0) > 2000:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "performance",
            "severity": "warning",
            "title": "High P95 latency",
            "description": f"P95 latency is {latency_analysis['p95_ms']}ms, exceeding 2000ms threshold.",
            "action": "Optimize response times. Consider caching, database query optimization, or scaling resources.",
        })

    # Increasing latency trend
    if trend.get("latency_direction") == "increasing" and trend.get("latency_r_squared", 0) > 0.3:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "trend",
            "severity": "warning",
            "title": "Latency trending upward",
            "description": f"Latency increasing at {trend['latency_slope_ms_per_hour']}ms/hour with {round(trend.get('latency_r_squared', 0) * 100)}% confidence.",
            "action": "Proactive investigation recommended before latency reaches critical thresholds.",
        })

    # Degrading availability
    if trend.get("availability_direction") == "degrading":
        priority += 1
        recs.append({
            "priority": priority,
            "category": "trend",
            "severity": "critical" if abs(trend.get("availability_delta_pct", 0)) > 10 else "warning",
            "title": "Availability degrading",
            "description": f"Availability dropped {abs(trend.get('availability_delta_pct', 0))}% between first and second half of the period.",
            "action": "Immediate attention required. Service reliability is declining.",
        })

    # Anomalies detected
    if anomalies.get("count", 0) > 5:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "anomaly",
            "severity": "warning",
            "title": f"{anomalies['count']} latency anomalies detected",
            "description": "Multiple latency spikes outside normal range detected.",
            "action": "Review anomaly timestamps for correlation with deployments, traffic spikes, or infrastructure changes.",
        })

    # Flapping service
    if failure_patterns.get("pattern") == "intermittent_flapping":
        priority += 1
        recs.append({
            "priority": priority,
            "category": "stability",
            "severity": "warning",
            "title": "Service flapping detected",
            "description": "Service is alternating between up and down states frequently.",
            "action": "Check for network instability, DNS issues, or resource contention. Consider increasing check interval.",
        })

    # Sustained outage
    if failure_patterns.get("pattern") == "sustained_outage":
        priority += 1
        recs.append({
            "priority": priority,
            "category": "outage",
            "severity": "critical",
            "title": "Sustained outage pattern",
            "description": f"Longest consecutive failure burst: {failure_patterns.get('max_consecutive_failures', 0)} checks.",
            "action": "Urgent: Service experienced prolonged downtime. Implement redundancy or failover mechanisms.",
        })

    # High latency variance
    if latency_analysis.get("cv_pct", 0) > 50:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "consistency",
            "severity": "info",
            "title": "High latency variance",
            "description": f"Coefficient of variation is {latency_analysis['cv_pct']}%, indicating inconsistent response times.",
            "action": "Investigate causes of response time variability. May indicate resource contention or variable load.",
        })

    # All good
    if not recs:
        recs.append({
            "priority": 0,
            "category": "health",
            "severity": "info",
            "title": "Service is healthy",
            "description": "No issues detected. All metrics within normal ranges.",
            "action": "Continue monitoring. No action required.",
        })

    return recs


def _compute_risk_score(
    availability_pct, latency_analysis, trend, anomalies, failure_patterns
) -> Dict:
    """Compute a 0-100 risk score (0=excellent, 100=critical)."""
    score = 0
    factors = []

    # Availability (0-35 points)
    if availability_pct < 100:
        avail_risk = min(35, (100 - availability_pct) * 3.5)
        score += avail_risk
        if avail_risk > 10:
            factors.append(f"Availability at {availability_pct}%")

    # Latency P95 (0-20 points)
    p95 = latency_analysis.get("p95_ms", 0)
    if p95 > 500:
        lat_risk = min(20, (p95 - 500) / 100)
        score += lat_risk
        if lat_risk > 5:
            factors.append(f"P95 latency at {p95}ms")

    # Trend (0-15 points)
    if trend.get("latency_direction") == "increasing":
        slope_risk = min(15, abs(trend.get("latency_slope_ms_per_hour", 0)) * 2)
        score += slope_risk
        if slope_risk > 3:
            factors.append("Latency trending up")

    if trend.get("availability_direction") == "degrading":
        score += 10
        factors.append("Availability degrading")

    # Anomalies (0-15 points)
    anom_count = anomalies.get("count", 0)
    if anom_count > 0:
        anom_risk = min(15, anom_count * 2)
        score += anom_risk
        if anom_risk > 3:
            factors.append(f"{anom_count} anomalies detected")

    # Failure patterns (0-15 points)
    pattern = failure_patterns.get("pattern", "none")
    if pattern == "sustained_outage":
        score += 15
        factors.append("Sustained outage pattern")
    elif pattern == "intermittent_flapping":
        score += 10
        factors.append("Flapping detected")
    elif pattern == "mixed":
        score += 5

    score = min(100, round(score))

    if score <= 20:
        level = "low"
        label = "Healthy"
    elif score <= 45:
        level = "moderate"
        label = "Needs Attention"
    elif score <= 70:
        level = "high"
        label = "At Risk"
    else:
        level = "critical"
        label = "Critical"

    return {
        "score": score,
        "level": level,
        "label": label,
        "factors": factors,
    }


def analyze_all_services(db: Session, hours: int = 24) -> Dict:
    """Global AI analysis summary across all external services."""
    services = db.query(ExternalService).filter(ExternalService.enabled == True).all()
    if not services:
        return {"status": "no_services", "services": [], "summary": {}}

    results = []
    risk_scores = []
    total_recs = []
    statuses = {"healthy": 0, "warning": 0, "critical": 0, "insufficient_data": 0}

    for svc in services:
        analysis = analyze_service(db, svc.id, hours)
        if analysis.get("status") == "insufficient_data":
            statuses["insufficient_data"] += 1
            results.append({
                "service_id": svc.id,
                "service_name": svc.name,
                "status": "insufficient_data",
                "risk_score": None,
            })
            continue

        risk = analysis.get("risk_score", {})
        risk_level = risk.get("level", "low")
        risk_val = risk.get("score", 0)
        risk_scores.append(risk_val)

        if risk_level == "critical":
            statuses["critical"] += 1
        elif risk_level in ("high", "moderate"):
            statuses["warning"] += 1
        else:
            statuses["healthy"] += 1

        total_recs.extend(analysis.get("recommendations", []))

        results.append({
            "service_id": svc.id,
            "service_name": svc.name,
            "service_type": analysis.get("service_type", "unknown"),
            "current_status": analysis.get("current_status", "unknown"),
            "availability_pct": analysis.get("availability_pct"),
            "risk_score": risk,
            "trend": analysis.get("trend", {}),
            "anomaly_count": analysis.get("anomalies", {}).get("count", 0),
            "failure_pattern": analysis.get("failure_patterns", {}).get("pattern", "none"),
            "top_recommendation": analysis.get("recommendations", [{}])[0] if analysis.get("recommendations") else None,
        })

    # Sort by risk score descending
    results.sort(key=lambda r: (r.get("risk_score", {}) or {}).get("score", 0), reverse=True)

    # Count critical/warning recommendations
    critical_recs = [r for r in total_recs if r.get("severity") == "critical"]
    warning_recs = [r for r in total_recs if r.get("severity") == "warning"]

    avg_risk = round(_mean(risk_scores), 1) if risk_scores else 0

    return {
        "summary": {
            "total_services": len(services),
            "healthy": statuses["healthy"],
            "warning": statuses["warning"],
            "critical": statuses["critical"],
            "insufficient_data": statuses["insufficient_data"],
            "avg_risk_score": avg_risk,
            "overall_health": "critical" if statuses["critical"] > 0 else "warning" if statuses["warning"] > 0 else "healthy",
            "total_recommendations": len(total_recs),
            "critical_recommendations": len(critical_recs),
            "warning_recommendations": len(warning_recs),
        },
        "services": results,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }