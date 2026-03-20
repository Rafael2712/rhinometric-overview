"""
Rhinometric Collector — Configuration

Loads settings from environment variables and optional YAML file.
Environment variables take precedence over YAML values.
"""

import os
import sys
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("rhyno.collector.config")


@dataclass
class CollectorConfig:
    api_url: str = ""
    service_key: str = ""
    telemetry_token: str = ""
    collect_interval: int = 15
    enable_metrics: bool = True
    enable_logs: bool = True
    enable_traces: bool = True
    environment: str = "production"
    hostname: str = field(default_factory=lambda: os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", "unknown"))

    def validate(self) -> None:
        errors: list[str] = []
        if not self.api_url:
            errors.append("RHYNO_API_URL is required")
        if not self.service_key:
            errors.append("RHYNO_SERVICE_KEY is required")
        if not self.telemetry_token:
            errors.append("RHYNO_TELEMETRY_TOKEN is required")
        if self.collect_interval < 1:
            errors.append("COLLECT_INTERVAL must be >= 1")
        if errors:
            for e in errors:
                logger.error(e)
            sys.exit(1)


def _parse_bool(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "on")


def load_config() -> CollectorConfig:
    """Load configuration from optional YAML then override with env vars."""
    cfg = CollectorConfig()

    # ── Optional YAML ──────────────────────────────────────────
    yaml_path = os.environ.get("RHYNO_CONFIG_FILE", "config.yaml")
    if os.path.isfile(yaml_path):
        try:
            import yaml  # type: ignore
            with open(yaml_path) as f:
                data = yaml.safe_load(f) or {}
            cfg.api_url = data.get("api_url", cfg.api_url)
            cfg.service_key = data.get("service_key", cfg.service_key)
            cfg.telemetry_token = data.get("telemetry_token", cfg.telemetry_token)
            cfg.collect_interval = int(data.get("collect_interval", cfg.collect_interval))
            cfg.environment = data.get("environment", cfg.environment)
            if "enable_metrics" in data:
                cfg.enable_metrics = bool(data["enable_metrics"])
            if "enable_logs" in data:
                cfg.enable_logs = bool(data["enable_logs"])
            if "enable_traces" in data:
                cfg.enable_traces = bool(data["enable_traces"])
            logger.info(f"Loaded YAML config from {yaml_path}")
        except ImportError:
            logger.warning("PyYAML not installed — skipping YAML config")
        except Exception as exc:
            logger.warning(f"Failed to load {yaml_path}: {exc}")

    # ── Environment overrides (always win) ─────────────────────
    cfg.api_url = os.environ.get("RHYNO_API_URL", cfg.api_url).rstrip("/")
    cfg.service_key = os.environ.get("RHYNO_SERVICE_KEY", cfg.service_key)
    cfg.telemetry_token = os.environ.get("RHYNO_TELEMETRY_TOKEN", cfg.telemetry_token)
    cfg.collect_interval = int(os.environ.get("COLLECT_INTERVAL", str(cfg.collect_interval)))
    cfg.environment = os.environ.get("RHYNO_ENVIRONMENT", cfg.environment)

    if "ENABLE_METRICS" in os.environ:
        cfg.enable_metrics = _parse_bool(os.environ["ENABLE_METRICS"])
    if "ENABLE_LOGS" in os.environ:
        cfg.enable_logs = _parse_bool(os.environ["ENABLE_LOGS"])
    if "ENABLE_TRACES" in os.environ:
        cfg.enable_traces = _parse_bool(os.environ["ENABLE_TRACES"])

    cfg.validate()
    return cfg
