"""
AI Analyzer for External Services — Intelligence Engine (Hardened v2).

Provides statistical analysis, anomaly detection, trend prediction,
and smart recommendations using check history data.
No external AI service required — uses pure statistical methods.

Hardening v2 changes:
  - MAD-based anomaly detection (replaces Gaussian Z-score)
  - Stricter trend confidence thresholds (R² >= 0.4)
  - Honest prediction semantics (no overstated "probabilities")
  - Minimum data requirements for all insight types
  - Less noisy risk scoring (persistent degradation > isolated spikes)
  - Reduced recommendation alarm level
  - TTL cache for /ai/summary endpoint (60s)
"""

import math
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from models.external_service import ExternalService, ServiceStatus
from models.external_service_check import ExternalServiceCheck

logger = logging.getLogger("rhinometric.ai_analyzer")

# ── Constants ────────────────────────────────────────────────────
TREND_WINDOW_HOURS = 24
ANOMALY_MAD_THRESHOLD = 5.0       # Modified Z-score threshold (MAD-based)
DEGRADATION_THRESHOLD_PCT = 20    # 20 % latency increase = degradation warning
PREDICTION_HOURS = 72             # Projection horizon

# ── Minimum-data gates ───────────────────────────────────────────
MIN_CHECKS_FOR_ANALYSIS = 10      # global gate — below this we say "insufficient data"
MIN_CHECKS_FOR_ANOMALY = 20       # anomaly detection needs ≥ 20 points
MIN_CHECKS_FOR_TREND = 10         # trend regression needs ≥ 10 points
MIN_TREND_TIME_SPAN_H = 2         # trend data must span ≥ 2 hours
TREND_R2_THRESHOLD = 0.4          # R² must be ≥ 0.4 to call trend meaningful
PREDICTION_R2_THRESHOLD = 0.3     # latency projection gate
MIN_CHECKS_FOR_PREDICTION = 30    # projections need >= 30 points
MIN_CHECKS_FOR_AVAIL_FORECAST = 50
MIN_CHECKS_FOR_FAILURE_PATTERN = 5

# ── Summary cache ────────────────────────────────────────────────
SUMMARY_CACHE_TTL = 60            # seconds
_summary_cache: Dict = {"data": None, "hours": None, "expires": 0.0}


# ═══════════════════════════════════════════════════════════════════
# Helper math functions
# ═══════════════════════════════════════════════════════════════════

def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0

def _std(values: List[float], mean_val: float) -> float:
    if len(values) < 2:
        return 0.0
    return math.sqrt(sum((v - mean_val) ** 2 for v in values) / (len(values) - 1))

def _median(sorted_values: List[float]) -> float:
    """Median of an already-sorted list."""
    n = len(sorted_values)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return sorted_values[n // 2]
    return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0

def _mad(values: List[float], median_val: float) -> float:
    """Median Absolute Deviation."""
    abs_devs = sorted(abs(v - median_val) for v in values)
    return _median(abs_devs)

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


# ═══════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════

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

    # ── Trend Detection (hardened) ──
    trend = _detect_trend(checks)

    # ── Anomaly Detection (MAD-based) ──
    anomalies = _detect_anomalies(checks, latencies)

    # ── Failure Patterns ──
    failure_patterns = _analyze_failure_patterns(checks)

    # ── Predictions (honest semantics) ──
    predictions = _generate_predictions(checks, latencies, svc)

    # ── Recommendations (less noisy) ──
    recommendations = _generate_recommendations(
        svc, availability_pct, latency_analysis, trend,
        anomalies, failure_patterns, predictions
    )

    # ── Risk Score (hardened) ──
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


# ═══════════════════════════════════════════════════════════════════
# Latency stats (unchanged structure)
# ═══════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════
# Trend detection  (HARDENED — R² gate + time span check)
# ═══════════════════════════════════════════════════════════════════

def _detect_trend(checks: List) -> Dict:
    """Detect latency and availability trends using linear regression.

    Hardened:
      - requires >= MIN_CHECKS_FOR_TREND data points
      - requires data spanning >= MIN_TREND_TIME_SPAN_H hours
      - only reports non-stable direction when R² >= TREND_R2_THRESHOLD
      - adds 'confidence' label
    """
    latency_points = [
        (c.checked_at.timestamp(), c.response_time_ms)
        for c in checks
        if c.response_time_ms and c.response_time_ms > 0
    ]

    insufficient = {"latency_direction": "insufficient_data", "availability_direction": "insufficient_data",
                     "confidence": "none"}

    if len(latency_points) < MIN_CHECKS_FOR_TREND:
        return insufficient

    # Check time span
    time_span_h = (latency_points[-1][0] - latency_points[0][0]) / 3600
    if time_span_h < MIN_TREND_TIME_SPAN_H:
        return insufficient

    x = [p[0] for p in latency_points]
    y = [p[1] for p in latency_points]
    slope, _, r_sq = _linear_regression(x, y)

    # Normalize slope to ms per hour
    slope_per_hour = slope * 3600

    # ── Hardened: only report direction if R² is strong enough ──
    if r_sq < TREND_R2_THRESHOLD or abs(slope_per_hour) < 0.5:
        lat_direction = "stable"
        confidence = "low" if r_sq < 0.2 else "weak"
    else:
        lat_direction = "increasing" if slope_per_hour > 0 else "decreasing"
        confidence = "moderate" if r_sq < 0.6 else "strong"

    # Availability trend: compare first half vs second half
    mid = len(checks) // 2
    first_half = checks[:mid]
    second_half = checks[mid:]
    avail_first = sum(1 for c in first_half if c.status == "up") / len(first_half) * 100 if first_half else 100
    avail_second = sum(1 for c in second_half if c.status == "up") / len(second_half) * 100 if second_half else 100
    avail_delta = avail_second - avail_first

    # Hardened: require > 3% delta (was 1%)
    if abs(avail_delta) < 3:
        avail_direction = "stable"
    elif avail_delta > 0:
        avail_direction = "improving"
    else:
        avail_direction = "degrading"

    return {
        "latency_direction": lat_direction,
        "latency_slope_ms_per_hour": round(slope_per_hour, 3),
        "latency_r_squared": round(r_sq, 3),
        "confidence": confidence,
        "availability_direction": avail_direction,
        "availability_first_half_pct": round(avail_first, 1),
        "availability_second_half_pct": round(avail_second, 1),
        "availability_delta_pct": round(avail_delta, 1),
    }


# ═══════════════════════════════════════════════════════════════════
# Anomaly detection  (REPLACED — MAD-based modified Z-score)
# ═══════════════════════════════════════════════════════════════════

def _detect_anomalies(checks: List, latencies: List[float]) -> Dict:
    """MAD-based modified Z-score anomaly detection.

    Much more robust than classical Z-score for right-skewed latency
    distributions.  A single moderate spike no longer creates a
    dramatic anomaly unless it is truly far from the robust center.

    Modified Z-score = 0.6745 * (x_i - median) / MAD
    Threshold: 3.5 (standard for MAD-based detection)

    Additional guard: a data point must deviate by at least 30 % from
    the median *and* exceed the MAD threshold.  This prevents tight
    distributions from producing hundreds of low-impact anomalies.
    """
    if len(latencies) < MIN_CHECKS_FOR_ANOMALY:
        return {
            "count": 0,
            "details": [],
            "status": "insufficient_data",
            "method": "mad",
            "message": f"Need >= {MIN_CHECKS_FOR_ANOMALY} samples, have {len(latencies)}",
        }

    sorted_lat = sorted(latencies)
    median_val = _median(sorted_lat)
    mad_val = _mad(latencies, median_val)

    if mad_val == 0:
        # All values identical or nearly so — no variance to detect against
        return {"count": 0, "details": [], "status": "no_variance", "method": "mad"}

    # Minimum absolute deviation: at least 30 % of median
    # This prevents tight distributions from flagging trivially small deviations.
    min_abs_deviation = median_val * 0.30

    anomaly_details = []
    for c in checks:
        if c.response_time_ms and c.response_time_ms > 0:
            deviation = c.response_time_ms - median_val
            abs_deviation = abs(deviation)
            modified_z = 0.6745 * deviation / mad_val
            abs_z = abs(modified_z)
            if abs_z >= ANOMALY_MAD_THRESHOLD and abs_deviation >= min_abs_deviation:
                severity = "critical" if abs_z >= 7.0 else "warning" if abs_z >= 6.0 else "info"
                anomaly_details.append({
                    "timestamp": c.checked_at.isoformat(),
                    "value_ms": round(c.response_time_ms, 2),
                    "z_score": round(abs_z, 2),      # keep field name for frontend compat
                    "direction": "high" if c.response_time_ms > median_val else "low",
                    "severity": severity,
                })

    return {
        "count": len(anomaly_details),
        "threshold": ANOMALY_MAD_THRESHOLD,
        "method": "mad",
        "median_ms": round(median_val, 2),
        "mad_ms": round(mad_val, 2),
        "details": anomaly_details[-10:],   # last 10 anomalies
    }


# ═══════════════════════════════════════════════════════════════════
# Failure patterns (lightly adjusted min-data gate)
# ═══════════════════════════════════════════════════════════════════

def _analyze_failure_patterns(checks: List) -> Dict:
    """Analyze failure distribution and patterns."""
    if len(checks) < MIN_CHECKS_FOR_FAILURE_PATTERN:
        return {"total_failures": 0, "pattern": "insufficient_data"}

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


# ═══════════════════════════════════════════════════════════════════
# Predictions  (HARDENED — honest semantics)
# ═══════════════════════════════════════════════════════════════════

def _generate_predictions(checks: List, latencies: List[float], svc) -> Dict:
    """Generate forward-looking projections with honest naming.

    Hardened changes:
      - "failure_probability" → "recent_failure_rate_pct" (observed rate, not a prediction)
      - latency projection only when R² >= PREDICTION_R2_THRESHOLD
      - availability estimate only when sample >= MIN_CHECKS_FOR_AVAIL_FORECAST
      - old field names kept as aliases for backward compatibility
    """
    predictions: Dict = {}

    # ── Latency projection (gated on R²) ──
    if len(latencies) >= MIN_CHECKS_FOR_PREDICTION:
        lat_points = [
            (c.checked_at.timestamp(), c.response_time_ms)
            for c in checks
            if c.response_time_ms and c.response_time_ms > 0
        ]
        if len(lat_points) >= MIN_CHECKS_FOR_TREND:
            x = [p[0] for p in lat_points]
            y = [p[1] for p in lat_points]
            slope, intercept, r_sq = _linear_regression(x, y)
            future_ts = datetime.now(timezone.utc).timestamp() + PREDICTION_HOURS * 3600
            projected = slope * future_ts + intercept

            if projected > 0 and r_sq >= PREDICTION_R2_THRESHOLD:
                predictions["latency_projection_72h_ms"] = round(projected, 2)
                predictions["latency_trend_confidence"] = round(r_sq, 2)
                # backward compat alias
                predictions["latency_72h_ms"] = predictions["latency_projection_72h_ms"]
            else:
                predictions["latency_projection_72h_ms"] = None
                predictions["latency_trend_confidence"] = round(r_sq, 2)
                predictions["latency_72h_ms"] = None

    # ── SSL monitoring (unchanged) ──
    if svc.service_type and svc.service_type.value == "http":
        config = svc.config or {}
        url = config.get("url", "")
        if url.startswith("https://"):
            predictions["ssl_monitoring"] = True

    # ── Recent failure rate (honest naming) ──
    recent = checks[-20:] if len(checks) >= 20 else checks
    recent_failures = sum(1 for c in recent if c.status in ("down", "error"))
    rate = round((recent_failures / len(recent)) * 100, 1) if recent else 0
    predictions["recent_failure_rate_pct"] = rate
    # backward compat alias — old frontend key
    predictions["failure_probability_next_hour_pct"] = rate

    # ── Availability estimate (honest naming, stricter gate) ──
    if len(checks) >= MIN_CHECKS_FOR_AVAIL_FORECAST:
        avail = sum(1 for c in checks if c.status == "up") / len(checks) * 100
        predictions["availability_estimate_24h_pct"] = round(avail, 2)
        # backward compat alias
        predictions["availability_forecast_24h_pct"] = predictions["availability_estimate_24h_pct"]

    return predictions


# ═══════════════════════════════════════════════════════════════════
# Recommendations  (HARDENED — less alarmist)
# ═══════════════════════════════════════════════════════════════════

def _generate_recommendations(
    svc, availability_pct, latency_analysis, trend,
    anomalies, failure_patterns, predictions
) -> List[Dict]:
    """Generate actionable recommendations with reduced noise.

    Hardened:
      - trend recommendations gated on R² > 0.5
      - anomaly recommendations require ≥ 3 warning+ anomalies
      - availability degradation requires ≥ 5 % delta
      - latency variance recommendation down-graded to info
      - severity language softened for weak signals
    """
    recs = []
    priority = 0

    # ── Availability issues ──
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

    # ── High latency ──
    if latency_analysis.get("p95_ms", 0) > 2000:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "performance",
            "severity": "warning",
            "title": "High P95 latency",
            "description": f"P95 latency is {latency_analysis['p95_ms']}ms, exceeding 2000ms threshold.",
            "action": "Review response times. Consider caching, query optimization, or scaling resources.",
        })

    # ── Increasing latency trend  (HARDENED: R² > 0.5 gate) ──
    if (trend.get("latency_direction") == "increasing"
            and trend.get("latency_r_squared", 0) > 0.5):
        priority += 1
        conf_label = trend.get("confidence", "moderate")
        recs.append({
            "priority": priority,
            "category": "trend",
            "severity": "warning" if conf_label == "strong" else "info",
            "title": "Latency trending upward",
            "description": (
                f"Latency increasing at {trend['latency_slope_ms_per_hour']}ms/hour "
                f"(R²={trend.get('latency_r_squared', 0)}, confidence: {conf_label})."
            ),
            "action": "Monitor closely. Proactive investigation recommended if trend persists.",
        })

    # ── Degrading availability  (HARDENED: need ≥ 5 % delta) ──
    avail_delta = abs(trend.get("availability_delta_pct", 0))
    if trend.get("availability_direction") == "degrading" and avail_delta >= 5:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "trend",
            "severity": "critical" if avail_delta > 15 else "warning" if avail_delta > 10 else "info",
            "title": "Availability degrading",
            "description": f"Availability dropped {avail_delta}% between first and second half of the period.",
            "action": "Investigate service reliability decline.",
        })

    # ── Anomalies  (HARDENED: need ≥ 3 warning+ anomalies) ──
    if anomalies.get("count", 0) > 0:
        warning_plus = [a for a in anomalies.get("details", []) if a.get("severity") in ("warning", "critical")]
        if len(warning_plus) >= 3:
            priority += 1
            recs.append({
                "priority": priority,
                "category": "anomaly",
                "severity": "warning",
                "title": f"{anomalies['count']} latency anomalies detected",
                "description": "Multiple latency spikes outside robust dispersion bounds detected.",
                "action": "Review anomaly timestamps for correlation with deployments, traffic spikes, or infrastructure changes.",
            })

    # ── Flapping service ──
    if failure_patterns.get("pattern") == "intermittent_flapping":
        priority += 1
        recs.append({
            "priority": priority,
            "category": "stability",
            "severity": "warning",
            "title": "Service flapping detected",
            "description": "Service is alternating between up and down states frequently.",
            "action": "Check for network instability, DNS issues, or resource contention.",
        })

    # ── Sustained outage ──
    if failure_patterns.get("pattern") == "sustained_outage":
        priority += 1
        recs.append({
            "priority": priority,
            "category": "outage",
            "severity": "critical",
            "title": "Sustained outage pattern",
            "description": f"Longest consecutive failure burst: {failure_patterns.get('max_consecutive_failures', 0)} checks.",
            "action": "Urgent: Implement redundancy or failover mechanisms.",
        })

    # ── High latency variance (info only) ──
    if latency_analysis.get("cv_pct", 0) > 50:
        priority += 1
        recs.append({
            "priority": priority,
            "category": "consistency",
            "severity": "info",
            "title": "High latency variance",
            "description": f"Coefficient of variation is {latency_analysis['cv_pct']}%, indicating inconsistent response times.",
            "action": "Investigate causes of response time variability.",
        })

    # ── All good ──
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


# ═══════════════════════════════════════════════════════════════════
# Risk score  (HARDENED — less sensitive to isolated spikes)
# ═══════════════════════════════════════════════════════════════════

def _compute_risk_score(
    availability_pct, latency_analysis, trend, anomalies, failure_patterns
) -> Dict:
    """Compute a 0-100 risk score (0=excellent, 100=critical).

    Hardened:
      - Trend contribution gated on R²
      - Anomaly contribution uses only warning+ anomalies and softer multiplier
      - Single-spike scenarios produce lower scores
      - Availability degradation requires ≥ 5 % delta
    """
    score = 0.0
    factors = []

    # ── Availability (0-35 points) — unchanged ──
    if availability_pct < 100:
        avail_risk = min(35, (100 - availability_pct) * 3.5)
        score += avail_risk
        if avail_risk > 10:
            factors.append(f"Availability at {availability_pct}%")

    # ── Latency P95 (0-20 points) — unchanged ──
    p95 = latency_analysis.get("p95_ms", 0)
    if p95 > 500:
        lat_risk = min(20, (p95 - 500) / 100)
        score += lat_risk
        if lat_risk > 5:
            factors.append(f"P95 latency at {p95}ms")

    # ── Trend (0-15 points) — HARDENED: gated on R² ──
    r_sq = trend.get("latency_r_squared", 0)
    if trend.get("latency_direction") == "increasing" and r_sq >= TREND_R2_THRESHOLD:
        slope_risk = min(15, abs(trend.get("latency_slope_ms_per_hour", 0)) * 2)
        score += slope_risk
        if slope_risk > 3:
            factors.append("Latency trending up")

    avail_delta = abs(trend.get("availability_delta_pct", 0))
    if trend.get("availability_direction") == "degrading" and avail_delta >= 5:
        score += min(10, avail_delta)
        factors.append("Availability degrading")

    # ── Anomalies (0-10 points) — HARDENED: warning+ only, softer multiplier ──
    warning_plus = [a for a in anomalies.get("details", []) if a.get("severity") in ("warning", "critical")]
    if warning_plus:
        anom_risk = min(10, len(warning_plus) * 1.5)
        score += anom_risk
        if anom_risk > 3:
            factors.append(f"{len(warning_plus)} significant anomalies")

    # ── Failure patterns (0-15 points) — unchanged ──
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


# ═══════════════════════════════════════════════════════════════════
# Global summary  (HARDENED — TTL cache)
# ═══════════════════════════════════════════════════════════════════

def analyze_all_services(db: Session, hours: int = 24) -> Dict:
    """Global AI analysis summary across all external services.

    Includes a lightweight in-process TTL cache (60 s) to avoid
    expensive re-computation on repeated requests.
    """
    global _summary_cache
    now = time.time()
    if (_summary_cache["data"] is not None
            and _summary_cache["hours"] == hours
            and now < _summary_cache["expires"]):
        logger.debug("[AI] Returning cached summary (TTL %.0fs remaining)",
                     _summary_cache["expires"] - now)
        return _summary_cache["data"]

    services = db.query(ExternalService).filter(ExternalService.enabled == True).all()
    if not services:
        empty = {"status": "no_services", "services": [], "summary": {}}
        _summary_cache.update({"data": empty, "hours": hours, "expires": now + SUMMARY_CACHE_TTL})
        return empty

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
                "monitoring_mode": svc.monitoring_mode.value if svc.monitoring_mode else "synthetic_only",
                "telemetry_status": svc.telemetry_status.value if svc.telemetry_status else "not_configured",
                "telemetry_attached": svc.telemetry_attached or False,
                "metrics_enabled": svc.metrics_enabled or False,
                "logs_enabled": svc.logs_enabled or False,
                "traces_enabled": svc.traces_enabled or False,
                "synthetic_enabled": svc.synthetic_enabled if svc.synthetic_enabled is not None else True,
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
            "monitoring_mode": svc.monitoring_mode.value if svc.monitoring_mode else "synthetic_only",
            "telemetry_status": svc.telemetry_status.value if svc.telemetry_status else "not_configured",
            "telemetry_attached": svc.telemetry_attached or False,
            "metrics_enabled": svc.metrics_enabled or False,
            "logs_enabled": svc.logs_enabled or False,
            "traces_enabled": svc.traces_enabled or False,
            "synthetic_enabled": svc.synthetic_enabled if svc.synthetic_enabled is not None else True,
        })

    # Sort by risk score descending
    results.sort(key=lambda r: (r.get("risk_score", {}) or {}).get("score", 0), reverse=True)

    # Count critical/warning recommendations
    critical_recs = [r for r in total_recs if r.get("severity") == "critical"]
    warning_recs = [r for r in total_recs if r.get("severity") == "warning"]

    avg_risk = round(_mean(risk_scores), 1) if risk_scores else 0

    result = {
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

    # ── Update TTL cache ──
    _summary_cache = {"data": result, "hours": hours, "expires": now + SUMMARY_CACHE_TTL}
    logger.debug("[AI] Summary computed and cached (TTL %ds)", SUMMARY_CACHE_TTL)
    return result
