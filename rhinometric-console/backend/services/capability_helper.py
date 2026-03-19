"""
Deterministic helper that derives a human-readable monitoring
capability label from the service's telemetry flags.

Used by the API response enrichment and (later) by the
frontend badges.
"""

from typing import Optional


def derive_capability(
    *,
    monitoring_mode: str = "synthetic_only",
    synthetic_enabled: bool = True,
    metrics_enabled: bool = False,
    logs_enabled: bool = False,
    traces_enabled: bool = False,
    telemetry_attached: bool = False,
) -> str:
    """
    Return one of:
      "Synthetic only"
      "Synthetic + Metrics"
      "Synthetic + Logs"
      "Synthetic + Traces"
      "Synthetic + Metrics & Logs"
      "Synthetic + Metrics & Traces"
      "Synthetic + Logs & Traces"
      "Synthetic + Full telemetry"
      "Metrics only"
      "Logs only"
      "Traces only"
      "Metrics & Logs"
      "Metrics & Traces"
      "Logs & Traces"
      "Full telemetry"
      "No monitoring"
    """
    signals: list[str] = []
    if metrics_enabled:
        signals.append("Metrics")
    if logs_enabled:
        signals.append("Logs")
    if traces_enabled:
        signals.append("Traces")

    has_synthetic = synthetic_enabled
    has_telemetry = len(signals) > 0

    if has_synthetic and has_telemetry:
        if len(signals) == 3:
            return "Synthetic + Full telemetry"
        return f"Synthetic + {' & '.join(signals)}"
    elif has_synthetic:
        return "Synthetic only"
    elif has_telemetry:
        if len(signals) == 3:
            return "Full telemetry"
        if len(signals) == 1:
            return f"{signals[0]} only"
        return " & ".join(signals)
    else:
        return "No monitoring"


def derive_capability_from_dict(svc: dict) -> str:
    """Convenience wrapper accepting a service dict."""
    return derive_capability(
        monitoring_mode=svc.get("monitoring_mode", "synthetic_only"),
        synthetic_enabled=svc.get("synthetic_enabled", True),
        metrics_enabled=svc.get("metrics_enabled", False),
        logs_enabled=svc.get("logs_enabled", False),
        traces_enabled=svc.get("traces_enabled", False),
        telemetry_attached=svc.get("telemetry_attached", False),
    )
